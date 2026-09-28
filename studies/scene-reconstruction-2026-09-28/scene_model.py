"""Finite-facet light transport and joint unknown xyz/reflectance inversion.

Known small-patch areas/normals/count. No texture, pose estimation, learned prior,
multiple reflections, or scene occlusion. Panel shadowing is checked separately.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import importlib.util
import numpy as np
from scipy.optimize import least_squares,linear_sum_assignment

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'layout-noise-2026-09-27/depth_benchmark.py'
spec=importlib.util.spec_from_file_location('geometry',SOURCE)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
MASKS=[d.CHECKER,~d.CHECKER,d.COLUMNS,~d.COLUMNS,d.ROWS,~d.ROWS]
NORM=np.array([0.,0.,-1.]);PATCH_AREA=1e-6

def rotation(rx=0.,ry=0.):
    x,y=np.deg2rad([rx,ry]);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y)
    return np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])

def poses(mode,heldout=False):
    moves=[[-20,0,0],[20,0,0],[0,-20,0],[0,20,0],[0,0,0]]
    if heldout:moves=[[-10,-10,0],[10,-10,0],[-10,10,0],[10,10,0]]
    out=[]
    for x,y,z in moves:
        t=np.array([x,y,z],float) if mode!='static' or heldout else np.zeros(3)
        R=rotation(-y*.5,x*.5) if mode=='rigid' or heldout else np.eye(3)
        out.append((R,t))
    return out

def make_panel(alpha):
    p=d.Panel('triangle',alpha,'vertical')
    f=np.sqrt(np.cos(np.deg2rad(alpha)))
    p.faces*=f;p.height*=f;p.side*=f;p.area*=f*f
    p.offsets=np.r_[p.normals[:,2]*p.height,0.]
    assert np.allclose(p.area.sum(),d.BASE_AREA)
    return p

class Acquisition:
    def __init__(self,panel,sequence,n=2,scale=1.,pose_budget=5):
        self.panel=panel;self.sequence=sequence;self.n=n;self.scale=scale
        local=panel.samples(n).reshape(48,n*n,3)
        norms=np.tile(panel.normals,(16,1))
        self.samples=np.array([local@R.T+t for R,t in sequence])
        self.normals=np.array([norms@R.T for R,t in sequence])
        self.areas=np.tile(panel.area,16)*1e-6
        self.emit=np.array([np.repeat(m,3) for m in MASKS])
        self.receiver=np.array([np.flatnonzero(~m) for m in self.emit])
        self.source_weight=self.emit.astype(float)/(pose_budget*6*3*24*np.pi)
        self.read_variance=16.
        self.rows=len(sequence)*6*24
    def forward(self,points,scene_normals=None,derivative=False):
        points=np.asarray(points);normals=np.tile(NORM,(len(points),1)) if scene_normals is None else np.asarray(scene_normals)
        r=points[None,None,None,:,:]-self.samples[:,:,:,None,:]
        r2=(r*r).sum(axis=-1)
        a=np.einsum('pfqjc,pfc->pfqj',r,self.normals)
        b=np.einsum('pfqjc,jc->pfqj',r,-normals)
        active=(a>0)&(b>0)
        k=np.where(active,a*b/r2**2,0)*1e6
        kernel=k.mean(axis=2)
        illumination=np.einsum('sf,pfj->psj',self.source_weight,kernel)
        receive=kernel[:,self.receiver,:]
        area=self.areas[self.receiver][None,:,:,None]
        operator=illumination[:,:,None,:]*receive*area*PATCH_AREA/np.pi*self.scale
        if not derivative:return operator.reshape(-1,len(points))
        dk=((self.normals[:,:,None,None,:]*b[:,:,:,:,None]-normals[None,None,None,:,:]*a[:,:,:,:,None])/r2[:,:,:,:,None]**2
            -4*a[:,:,:,:,None]*b[:,:,:,:,None]*r/r2[:,:,:,:,None]**3)*1e6
        dk*=active[:,:,:,:,None];dk=dk.mean(axis=2)
        di=np.einsum('sf,pfjc->psjc',self.source_weight,dk)
        dr=dk[:,self.receiver,:,:]
        grad=(di[:,:,None,:,:]*receive[:,:,:,:,None]+illumination[:,:,None,:,None]*dr)*area[:,:,:,:,None]*PATCH_AREA/np.pi*self.scale
        return operator.reshape(-1,len(points)),grad.reshape(-1,len(points),3)
    def background(self,exchange,eta):
        block=[]
        for si,emit in enumerate(self.emit):
            # Same source allocation as useful transport, without the Lambert pi twice.
            block.append(exchange[emit][:,~emit].sum(axis=0)*self.source_weight[si,emit][0]*np.pi*self.scale*eta)
        return np.tile(np.concatenate(block),len(self.sequence))
    def shadow_fraction(self,points):
        fractions=[]
        local=self.panel.samples(self.n).reshape(-1,3)
        owners=np.repeat(np.arange(16),3*self.n*self.n)
        norms=np.repeat(np.tile(self.panel.normals,(16,1)),self.n*self.n,axis=0)
        for R,t in self.sequence:
            transformed=(points-t)@R
            for pt in transformed:
                rays=np.tile(pt,(len(local),1));delta=rays-local
                active=np.einsum('ij,ij->i',delta,norms)>0
                visible=self.panel.visible(local,rays,owners)
                fractions.append(float(np.mean(~visible[active])) if active.any() else 0.)
        return max(fractions)

def calibration():
    reference=Acquisition(make_panel(15),poses('static'),n=4)
    return float(100000/(reference.forward([[0.,0.,150.]]).sum()*3))

def matched_errors(points,rho,truth_points,truth_rho):
    distances=np.linalg.norm(np.asarray(points)[:,None,:]-np.asarray(truth_points)[None,:,:],axis=-1)
    row,col=linear_sum_assignment(distances)
    reordered=np.zeros_like(truth_points,dtype=float);colours=np.zeros_like(truth_rho,dtype=float)
    reordered[col]=np.asarray(points)[row];colours[col]=np.asarray(rho)[row]
    errors=np.linalg.norm(reordered-truth_points,axis=1)
    return {'matched_points_mm':reordered.tolist(),'matched_rho':colours.tolist(),'xyz_rmse_mm':float(np.sqrt(np.mean(errors**2))),
      'depth_rmse_mm':float(np.sqrt(np.mean((reordered[:,2]-np.asarray(truth_points)[:,2])**2))),
      'reflectance_rmse':float(np.sqrt(np.mean((colours-truth_rho)**2))),'point_errors_mm':errors.tolist()}

def initializations(count,starts,seed):
    rng=np.random.default_rng(seed);out=[]
    for i in range(starts):
        p=rng.uniform([-35,-25,35],[35,25,135],(count,3))
        if i==0:p=np.c_[np.linspace(-25,25,count),np.zeros(count),np.full(count,80.)]
        colour=rng.uniform(.15,.75,(count,3))
        out.append(np.c_[p,colour].ravel())
    return out

def fit(acq,observation,background,starts,max_nfev=220):
    count=len(starts[0])//6;w=1/np.sqrt(np.maximum(observation,1)+acq.read_variance)
    lower=np.tile([-50,-40,25,0,0,0],count);upper=np.tile([50,40,160,1,1,1],count)
    xscale=np.tile([40,40,80,.5,.5,.5],count)
    solutions=[]
    cache={}
    def evaluate(x):
        if 'x' in cache and np.array_equal(cache['x'],x):return cache['r'],cache['j']
        state=x.reshape(count,6);F,gradient=acq.forward(state[:,:3],derivative=True)
        predicted=F@state[:,3:]+background[:,None]
        J=np.zeros((acq.rows,3,count,6))
        J[:,:,:,:3]=np.einsum('rkd,kc->rckd',gradient,state[:,3:])
        for c in range(3):J[:,c,:,3+c]=F
        residual=((predicted-observation)*w).ravel();jac=(J*w[:,:,None,None]).reshape(-1,count*6)
        cache.update(x=x.copy(),r=residual,j=jac)
        return residual,jac
    for x0 in starts:
        fit=least_squares(lambda x:evaluate(x)[0],x0,jac=lambda x:evaluate(x)[1],bounds=(lower,upper),x_scale=xscale,
          max_nfev=max_nfev,ftol=1e-8,xtol=1e-8,gtol=1e-7)
        x=fit.x.reshape(count,6)
        scaled_sv=np.linalg.svd(fit.jac*xscale[None,:],compute_uv=False)
        solutions.append({'points_mm':x[:,:3].tolist(),'rho':x[:,3:].tolist(),'cost':float(2*fit.cost),'success':bool(fit.success),
          'status':int(fit.status),'nfev':fit.nfev,'optimality':float(fit.optimality),
          'boundary':bool(np.any((fit.x-lower)/(upper-lower)<1e-4)|np.any((upper-fit.x)/(upper-lower)<1e-4)),
          'scaled_jacobian_singular_values':scaled_sv.tolist()})
    best=min(solutions,key=lambda r:r['cost'])
    alternatives=[]
    for sol in solutions:
        if sol is best:continue
        if sol['cost']<=best['cost']+max(1.,best['cost']*.01):
            err=matched_errors(sol['points_mm'],sol['rho'],np.array(best['points_mm']),np.array(best['rho']))
            alternatives.append({'cost':sol['cost'],'xyz_distance_from_best_mm':err['xyz_rmse_mm'],'success':sol['success']})
    return {'best':best,'solutions':solutions,'near_cost_alternatives':alternatives,
      'ambiguity_rule':'objective within max(1,1% of minimum); heuristic, not confidence region; finite starts cannot establish uniqueness'}
