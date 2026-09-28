"""Synthetic shape/layout/crosstalk ablation. No physical sensor measurements.

python depth_benchmark.py --trials 48
Units: geometry mm; radiometric kernel internally converted to m^-2.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import argparse, importlib.util, json, math, time
import numpy as np
from scipy.optimize import least_squares, lsq_linear

OUT=Path(__file__).resolve().parent
OLD=OUT.parent/'facet-motion-2026-09-26/model.py'
spec=importlib.util.spec_from_file_location('old_inverse',OLD)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
BASE_AREA=np.sqrt(3)/4*9**2
CELL_AREA=np.sqrt(3)/2*10**2
ALPHAS=[30.,45.,math.degrees(math.atan(14/11))]
DEPTH_GRID=np.arange(20.,201.,1.)
SEARCH_GRID=DEPTH_GRID[::2]
POSES=np.array([[-20.,0.,0.],[0.,0.,0.],[20.,0.,0.]])
TRUE_RGB=np.array([[.75,.15,.10],[.10,.30,.75]])
SCENES={
 'central':{'xy':[[-18.,-8.],[18.,8.]],'z':[111.3,156.7]},
 'oblique':{'xy':[[65.,-15.],[95.,15.]],'z':[80.7,117.3]},
 'grazing':{'xy':[[90.,-15.],[110.,15.]],'z':[30.3,50.7]},
}
PIXEL_RC=np.array([[r,c] for r in range(4) for c in range(4)])
CHECKER=(PIXEL_RC.sum(axis=1)%2)==0
COLUMNS=(PIXEL_RC[:,1]%2)==0
ROWS=(PIXEL_RC[:,0]%2)==0


def triangle_samples(faces,n):
    uv=[]
    for i in range(n):
        for j in range(n-i):
            uv.append([(i+1/3)/n,(j+1/3)/n])
            if i+j<=n-2:uv.append([(i+2/3)/n,(j+2/3)/n])
    uv=np.array(uv)
    return faces[:,0,None,:]+uv[None,:,:1]*(faces[:,1]-faces[:,0])[:,None,:]+uv[None,:,1:]*(faces[:,2]-faces[:,0])[:,None,:]


class Panel:
    def __init__(self,shape,alpha,layout):
        self.shape,self.alpha,self.layout=shape,alpha,layout
        self.k=3 if shape=='triangle' else 4
        self.repeats=12//self.k
        self.read_variance=self.repeats*2.**2
        az=np.deg2rad([90,210,330] if self.k==3 else [0,90,180,270])
        self.side=9. if self.k==3 else np.sqrt(BASE_AREA)
        radius=self.side/(np.sqrt(3) if self.k==3 else np.sqrt(2))
        inradius=self.side/(2*np.sqrt(3)) if self.k==3 else self.side/2
        self.height=inradius*np.tan(np.deg2rad(alpha))
        vertices=np.vstack([np.c_[radius*np.cos(az),radius*np.sin(az),np.zeros(self.k)], [0,0,self.height]])
        faces=vertices[np.array([[i,(i+1)%self.k,self.k] for i in range(self.k)])]
        cross=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        self.normals=cross/np.linalg.norm(cross,axis=1)[:,None]
        self.area=np.linalg.norm(cross,axis=1)/2
        assert np.allclose(self.area.sum(),BASE_AREA/np.cos(np.deg2rad(alpha)))
        self.faces=faces
        q=np.sqrt(CELL_AREA)
        sx,sy=(10*np.sqrt(3)/2,10.) if layout=='vertical' else (q,q)
        self.centers=np.array([[sx*c,sy*(r+(.5*(c%2) if layout in ['vertical','shifted'] else 0)),0] for r,c in PIXEL_RC])
        self.centers-=self.centers.mean(axis=0)
        # Separating-axis check: reject physically overlapping bases.
        poly=vertices[:-1,:2]
        edges=np.roll(poly,-1,axis=0)-poly
        axes=np.c_[-edges[:,1],edges[:,0]]
        for i in range(16):
            for j in range(i):
                a=(poly+self.centers[i,:2])@axes.T
                b=(poly+self.centers[j,:2])@axes.T
                assert np.any((a.max(axis=0)<=b.min(axis=0)+1e-10)|(b.max(axis=0)<=a.min(axis=0)+1e-10)),'Overlapping bases'
        self.planes=np.vstack([self.normals,[0,0,-1]])
        self.offsets=np.r_[self.normals[:,2]*self.height,0]
        self.id=f'{shape}-{layout}-{alpha:.6f}'

    def samples(self,n):
        return self.centers[:,None,None,:]+triangle_samples(self.faces,n)[None,:,:,:]

    def visible(self,starts,ends,owner_start,owner_end=None):
        """Segment vs convex bodies; ignore endpoint owners, Lambert positive only.

        Starts/ends have shape(N,3). Missing occluders beyond the finite 4x4
        panel are intentional; angular benchmark separately uses periodic panel.
        """
        visible=np.ones(len(starts),dtype=bool)
        delta=ends-starts
        den=delta@self.planes.T
        positive=den>1e-12;negative=den < -1e-12
        parallel=~(positive|negative)
        for idx,center in enumerate(self.centers):
            ids=np.flatnonzero(visible & (owner_start!=idx) & (True if owner_end is None else owner_end!=idx))
            if not len(ids):continue
            num=self.offsets-(starts[ids]-center)@self.planes.T
            with np.errstate(divide='ignore',invalid='ignore'):
                values=num/den[ids]
            enter=np.max(np.where(negative[ids],values,-np.inf),axis=1)
            leave=np.min(np.where(positive[ids],values,np.inf),axis=1)
            hit=(leave>=np.maximum(enter,1e-8))&(enter<1-1e-8)
            hit &= np.all(~parallel[ids] | (num>=-1e-9),axis=1)
            visible[ids[hit]]=False
        return visible

    def kernel(self,points,n=2,occlusion=True):
        """Patch-facing -z, finite facet sampling; per-facet kernel in m^-2."""
        s=self.samples(n)
        shape=(16,self.k,n*n,len(points))
        start=np.broadcast_to(s[:,:,:,None,:],shape+(3,)).reshape(-1,3)
        end=np.broadcast_to(np.asarray(points)[None,None,None,:,:],shape+(3,)).reshape(-1,3)
        own=np.broadcast_to(np.arange(16)[:,None,None,None],shape).ravel()
        norm=np.broadcast_to(self.normals[None,:,None,None,:],shape+(3,)).reshape(-1,3)
        delta=end-start;d2=(delta*delta).sum(axis=1)
        cos=np.einsum('ij,ij->i',delta,norm)/np.sqrt(d2)
        target_cos=delta[:,2]/np.sqrt(d2)
        val=np.maximum(cos,0)*np.maximum(target_cos,0)/d2*1e6
        active=np.flatnonzero(val>0)
        if occlusion:
            for chunk in np.array_split(active,max(1,math.ceil(len(active)/32768))):
                val[chunk]*=self.visible(start[chunk],end[chunk],own[chunk])
        return val.reshape(shape).mean(axis=2)

    def forward(self,points,n=2,occlusion=True,mask=CHECKER):
        blocks=[]
        # Total energy 1 shared over 3 poses,2 role slots,3 ideal spectral bands.
        for pose in POSES:
            g=self.kernel(np.asarray(points)-pose,n,occlusion)
            for emit in [mask,~mask]:
                illumination=g[emit].sum(axis=(0,1))/(3*2*3*8*self.k*np.pi)
                receive=g[~emit].reshape(-1,len(points))
                areas=np.tile(self.area,8)*1e-6
                blocks.append(illumination[None,:]/np.pi*1e-6*areas[:,None]*receive)
        return np.concatenate(blocks)

    def exchange(self,n=4):
        """Fraction of each uniformly emitting facet's energy reaching each other.

        F[e,r] = A_r/pi * double surface-average cos_e*cos_r*V/d².
        Includes other pyramids as opaque blockers; no reflection/cover layer.
        """
        s=self.samples(n).reshape(16*self.k,n*n,3)
        ns=np.tile(self.normals,(16,1));owners=np.repeat(np.arange(16),self.k)
        areas=np.tile(self.area,16)
        nf=len(s);f=np.zeros((nf,nf))
        for e in range(nf):
            rs=np.flatnonzero(owners!=owners[e])
            shape=(len(rs),n*n,n*n)
            starts=np.broadcast_to(s[e][None,:,None,:],shape+(3,)).reshape(-1,3)
            ends=np.broadcast_to(s[rs,None,:,:],shape+(3,)).reshape(-1,3)
            destnorm=np.broadcast_to(ns[rs,None,None,:],shape+(3,)).reshape(-1,3)
            ownr=np.broadcast_to(owners[rs,None,None],shape).ravel()
            delta=ends-starts;d2=(delta*delta).sum(axis=1)
            ce=delta@ns[e]/np.sqrt(d2)
            cr=-np.einsum('ij,ij->i',delta,destnorm)/np.sqrt(d2)
            value=np.maximum(ce,0)*np.maximum(cr,0)/d2
            active=np.flatnonzero(value>0)
            if len(active):
                value[active]*=self.visible(starts[active],ends[active],np.full(len(active),owners[e]),ownr[active])
            f[e,rs]=value.reshape(shape).mean(axis=(1,2))*areas[rs]/np.pi
        assert f.min()>=0
        assert f.sum(axis=1).max()<1+1e-4, 'Energy conservation failure'
        assert np.allclose(areas[:,None]*f,areas[None,:]*f.T,rtol=1e-9,atol=1e-10),'Reciprocity failure'
        return f

    def leakage(self,f,mask=CHECKER):
        v=[]
        for emit in [mask,~mask]:
            em=np.repeat(emit,self.k);rx=~em
            # Fraction per band/slot/pose, same emission budget as forward.
            v.append(f[em][:,rx].sum(axis=0)/(3*2*3*8*self.k))
        return np.tile(np.concatenate(v),3)


def prepare_tables(panel,scene,n):
    xy=np.array(scene['xy']);z=np.array(scene['z'])
    grids=[panel.forward(np.c_[np.tile(xy[p],(len(DEPTH_GRID),1)),DEPTH_GRID],n=n) for p in range(2)]
    truth=panel.forward(np.c_[xy,z],n=n)
    return grids,truth


def interpolate(grids,z):
    lo=np.clip(np.floor(z-DEPTH_GRID[0]).astype(int),0,len(DEPTH_GRID)-2)
    frac=np.asarray(z)-DEPTH_GRID[lo]
    return np.column_stack([(1-frac[p])*grids[p][:,lo[p]]+frac[p]*grids[p][:,lo[p]+1] for p in range(2)])


def fit(observed,subtraction,expected_background,grids,read_var):
    # Shot noise belongs to the raw intensity, even after mean subtraction.
    y=observed-subtraction[:,None]
    w=1/np.sqrt(np.maximum(observed,1.)+read_var)
    # Old profiling solver accepts any channel count and 3 bands.
    obj=old.profiles(grids[0][:,::2],grids[1][:,::2],y,w)
    iz=np.unravel_index(np.argmin(obj),obj.shape)
    z0=SEARCH_GRID[list(iz)]
    ff=interpolate(grids,z0)
    rho=np.column_stack([lsq_linear(ff*w[:,b,None],y[:,b]*w[:,b],bounds=(0,1),tol=1e-8).x for b in range(3)])
    initial=np.r_[z0,np.clip(rho.ravel(),1e-8,1-1e-8)]
    def residual(x):return ((interpolate(grids,x[:2])@x[2:].reshape(2,3)-y)*w).ravel()
    best=least_squares(residual,initial,bounds=([20,20]+[0]*6,[200,200]+[1]*6),
                       x_scale=[100,100]+[1]*6,max_nfev=180,ftol=1e-9,xtol=1e-9,gtol=1e-8)
    return {'z_mm':best.x[:2].tolist(),'rgb':best.x[2:].reshape(2,3).tolist(),
            'success':bool(best.success),'weighted_residual':float(2*best.cost)}


def information(grids,scene,scale_background,read_var):
    z=np.array(scene['z'])
    g=interpolate(grids,z);signal=g@TRUE_RGB
    # Derivative of interpolated model; scale in electrons/mm.
    lo=np.clip(np.floor(z-20).astype(int),0,len(DEPTH_GRID)-2)
    w=1/np.sqrt(signal+scale_background[:,None]+read_var)
    jz=np.column_stack([((grids[p][:,lo[p]+1]-grids[p][:,lo[p]])[:,None]*TRUE_RGB[p]*w).ravel() for p in range(2)])
    ja=[]
    for p in range(2):
        for c in range(3):
            v=np.zeros_like(signal);v[:,c]=g[:,p];ja.append((v*w).ravel())
    ja=np.array(ja).T
    jz-=ja@np.linalg.lstsq(ja,jz,rcond=None)[0]
    sv=np.linalg.svd(jz,compute_uv=False)
    return {'singular_values_per_mm':sv.tolist(),
            'local_depth_std_mm':np.sqrt(np.diag(np.linalg.pinv(jz.T@jz))).tolist()}


def main():
    args=argparse.ArgumentParser();args.add_argument('--trials',type=int,default=48)
    args.add_argument('--facet-n',type=int,default=4)
    options=args.parse_args();started=time.perf_counter()
    OUT.mkdir(exist_ok=True,parents=True)
    # One reference in a separate configuration sets ALL electron scales.
    reference=Panel('triangle',30.,'aligned')
    ref=reference.forward([[0,0,150]],n=options.facet_n)
    scale=100000/(3*ref.sum())
    levels=[0.,1e-6,1e-4]
    rows=[];geometry=[];selected={};rng=np.random.default_rng(270927)
    for shape in ['triangle','diamond']:
      for alpha in ALPHAS:
       for layout in ['aligned','shifted','vertical']:
        panel=Panel(shape,alpha,layout)
        f=panel.exchange(n=4)
        leakage=panel.leakage(f)*scale
        geo={'id':panel.id,'shape':shape,'tilt_deg':alpha,'layout':layout,
             'height_mm':panel.height,'base_area_mm2':BASE_AREA,'facet_area_total_mm2':float(panel.area.sum()),
             'readouts_per_band':3*2*8*12,'aggregated_channels_per_band':3*2*8*panel.k,
             'subexposures_per_slot':panel.repeats,'aggregated_channel_read_variance':panel.read_variance,
             'max_source_energy_fraction_to_other_pixels':float(f.sum(axis=1).max()),
             'leakage_fraction_all_bands':float(panel.leakage(f).sum()*3),
             'schedule_leakage_fraction_all_bands':{name:float(panel.leakage(f,mask).sum()*3) for name,mask in [('checker',CHECKER),('columns',COLUMNS),('rows',ROWS)]}}
        # Every source/receiver pair is integrated both ways, checks reciprocal.
        geometry.append(geo)
        for name,scene in SCENES.items():
            rawgrids,truth=prepare_tables(panel,scene,options.facet_n)
            grids=[g*scale for g in rawgrids]
            mu=truth*scale@TRUE_RGB
            interp_mu=interpolate(grids,scene['z'])@TRUE_RGB
            no_noise=fit(mu,np.zeros_like(leakage),np.zeros_like(leakage),grids,panel.read_variance)
            for attenuation in levels:
                bg=leakage*attenuation
                allfits=[]
                for trial in range(options.trials):
                    observed=rng.poisson(mu+bg[:,None]).astype(float)+rng.normal(0,np.sqrt(panel.read_variance),mu.shape)
                    estimate=fit(observed,bg,bg,grids,panel.read_variance)
                    allfits.append(estimate)
                errors=np.abs(np.array([q['z_mm'] for q in allfits])-scene['z'])
                row={'id':panel.id,'shape':shape,'tilt_deg':alpha,'layout':layout,'scene':name,
                     'optical_leakage_transmission':attenuation,'trials':options.trials,
                     'signal_electrons':float(mu.sum()),'background_electrons':float(3*bg.sum()),
                     'background_to_signal':float(3*bg.sum()/mu.sum()),
                     'median_mean_absolute_depth_error_mm':float(np.median(errors.mean(axis=1))),
                     'mean_absolute_depth_error_mm':float(errors.mean()),
                     'p90_mean_absolute_depth_error_mm':float(np.quantile(errors.mean(axis=1),.9)),
                     'failure_gt10mm_fraction':float(np.mean(errors.max(axis=1)>10)),
                     'median_rgb_absolute_error':float(np.median(np.abs(np.array([q['rgb'] for q in allfits])-TRUE_RGB))),
                     'nonconverged':sum(not q['success'] for q in allfits),
                     'grid_interpolation_relative_l2':float(np.linalg.norm(mu-interp_mu)/np.linalg.norm(mu)),
                     'noiseless_fit':no_noise,'information':information(grids,scene,bg,panel.read_variance),
                     'estimates':allfits}
                rows.append(row)
            # One fixed 0.1% relative subtraction error per channel; diagnostic.
            if name=='central' and alpha==45:
                gainer=np.random.default_rng(193)
                sloterr=gainer.normal(0,.001,2*8*panel.k)
                error=np.tile(sloterr,3)
                bg=leakage*1e-4
                selected[panel.id]={'known_subtraction_noiseless':fit(mu+bg[:,None],bg,bg,grids,panel.read_variance),
                                    'wrong_subtraction_noiseless':fit(mu+bg[:,None],bg*(1+error),bg,grids,panel.read_variance),
                                    'background_to_signal':float(bg.sum()*3/mu.sum())}
            print(json.dumps({'id':panel.id,'scene':name,'signal_e':round(float(mu.sum())),
                              'results':[{k:r[k] for k in ['optical_leakage_transmission','background_to_signal','median_mean_absolute_depth_error_mm']} for r in rows[-3:]],
                              'elapsed_s':round(time.perf_counter()-started)},ensure_ascii=False),flush=True)
        (OUT/'depth-progress.json').write_text(json.dumps({'finished_geometry':geometry,'rows':rows,'calibration_mismatch':selected},indent=2),encoding='utf-8')
    result={'status':'synthetic restricted geometry/crosstalk study; no device measurements',
            'parameters':{'seed':270927,'scenes':SCENES,'truth_rgb':TRUE_RGB.tolist(),'poses_mm':POSES.tolist(),
                          'depth_grid_mm':[20,200,1],'trials_per_condition':options.trials,
                          'facet_quadrature_samples':options.facet_n**2,'direct_coupling_samples_per_facet':16,
                          'reference_expected_electrons':100000,'shared_electron_scale':float(scale),
                          'common_allocated_panel_envelope_mm':[40,48],
                          'raw_read_noise_electrons_rms':2,'raw_readouts_per_pixel_slot_band':12,
                          'optical_leakage_transmissions':levels},
            'geometry':geometry,'rows':rows,'calibration_mismatch':selected,'elapsed_seconds':time.perf_counter()-started}
    (OUT/'depth-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'rows':len(rows),'fits':len(rows)*options.trials,'elapsed_seconds':result['elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
