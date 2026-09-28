"""Restricted synthetic depth/colour study, not a hardware performance forecast.

Run with Python + numpy + scipy + matplotlib. All results are generated locally.
Same model generates and fits data; calibration mismatch is tested separately.
"""
from __future__ import annotations
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MPLCONFIGDIR', str(__import__('pathlib').Path(__file__).parent / 'mpl-cache'))
import json
import time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares, nnls
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
XY = np.array([[-18., -8.], [18., 8.]])  # known, not reconstructed
TRUE_Z = np.array([111.3, 156.7])  # deliberately not on the 2 mm search grid
TRUE_RGB = np.array([[.75, .15, .10], [.10, .30, .75]])
ZGRID = np.arange(80., 191., 2.)
TRIALS = 32
READ_NOISE = 2.0  # hypothetical electrons RMS, same for every recorded value
AZ = np.deg2rad([30., 150., 270.])
BASE = 9.0
BASE_AREA = np.sqrt(3) * BASE**2 / 4  # mm2
PATCH_AREA = 1e-6  # m2
PIXELS = np.array([[np.sqrt(3)/2 * 10*c, 10*(r+.5*(c%2)), 0.]
                   for r in range(4) for c in range(4)])
PIXELS -= PIXELS.mean(axis=0)
PARITY = np.array([(r+c)%2 == 0 for r in range(4) for c in range(4)])
STATIC = [np.array([0., 0., 0.])] * 3
MOVING = [np.array([x, 0., 0.]) for x in [-20., 0., 20.]]
HELD_OUT = [np.array([0., 20., 0.])] * 3
CONFIGS = [(a, move) for a in [0., 30., 45.] for move in [False, True]]


def normals(alpha):
    a = np.deg2rad(alpha)
    return np.c_[np.sin(a)*np.cos(AZ), np.sin(a)*np.sin(AZ), np.full(3, np.cos(a))]


def forward(points_mm, alpha, poses):
    """Return M x N radiometric coefficients per unit band reflectance.

    All facets co-located at pixel centres. All three emitter facets radiate
    equal shares of pixel energy with individual Lambertian angular patterns.
    Total emitted optical energy fixed: 3 poses x 2 slots x 3 ideal bands.
    Actual facet area varies with tilt; footprint/frontal projected area fixed.
    Each of 8 receiving WHOLE pixels provides 3 separate facet measurements.
    """
    targets = np.atleast_2d(points_mm) * 1e-3
    n = normals(alpha)
    area = BASE_AREA / (3*np.cos(np.deg2rad(alpha))) * 1e-6
    energy = 1. / (len(poses)*2*3)  # total all bands, slots, poses = 1
    blocks = []
    for pose in poses:
        p = (PIXELS + pose) * 1e-3
        for emit_mask in [PARITY, ~PARITY]:
            de = targets[:, None, :] - p[None, emit_mask, :]
            re2 = np.sum(de**2, axis=-1)
            ue = de/np.sqrt(re2)[..., None]
            # 8 pixels x 3 source facets, each with the same energy share.
            emitter_cos = np.maximum(ue @ n.T, 0).sum(axis=-1)
            illum = (energy/(8*3*np.pi) * emitter_cos * ue[..., 2]/re2).sum(axis=1)
            dr = targets[:, None, :] - p[None, ~emit_mask, :]
            rr2 = np.sum(dr**2, axis=-1)
            ur = dr/np.sqrt(rr2)[..., None]
            receive_cos = np.maximum(ur @ n.T, 0)
            s = (illum[:, None, None]/np.pi * PATCH_AREA * area
                 * ur[..., 2, None] * receive_cos/rr2[..., None])
            blocks.append(s.reshape(len(targets), -1))
    return np.concatenate(blocks, axis=1).T


def points(z):
    return np.c_[XY, z]


def profiles(f0, f1, y, weights):
    """Exact two-column box-constrained LS over every depth pair, each band.

    Reflectance constraints 0 <= rho <= 1. Interior or one of four edges.
    Returns summed objectives for all grid pairs (n0,n1).
    """
    objective = np.zeros((f0.shape[1], f1.shape[1]))
    for band in range(3):
        w = weights[:, band]
        a, b, v = f0*w[:, None], f1*w[:, None], y[:, band]*w
        aa = (a*a).sum(axis=0)[:, None]
        bb = (b*b).sum(axis=0)[None, :]
        ab = a.T @ b
        av, bv = (a.T @ v)[:, None], (b.T @ v)[None, :]
        vv = v @ v
        det = aa*bb-ab*ab
        c0 = (av*bb-bv*ab)/np.maximum(det, np.finfo(float).tiny)
        c1 = (bv*aa-av*ab)/np.maximum(det, np.finfo(float).tiny)
        def score(x, z):
            return vv + aa*x*x+bb*z*z+2*ab*x*z-2*av*x-2*bv*z
        best = np.where((c0>=0)&(c0<=1)&(c1>=0)&(c1<=1)&(det>1e-12*aa*bb),
                        score(c0,c1), np.inf)
        for fixed in [0., 1.]:
            best = np.minimum(best, score(fixed, np.clip((bv-ab*fixed)/bb,0,1)))
            best = np.minimum(best, score(np.clip((av-ab*fixed)/aa,0,1),fixed))
        objective += np.maximum(best, 0)
    return objective


def fit(y, alpha, poses, scale, grids):
    # Feasible estimate of measurement variance, not oracle true counts.
    weights = 1/np.sqrt(np.maximum(y, 1.) + READ_NOISE**2)
    objective = profiles(*grids, y, weights)
    iz = np.unravel_index(np.argmin(objective), objective.shape)
    z0 = ZGRID[list(iz)]
    f = forward(points(z0), alpha, poses)*scale
    rho0 = np.column_stack([np.clip(nnls(f*weights[:, c, None], y[:, c]*weights[:, c])[0],
                                    1e-7, 1-1e-7) for c in range(3)])
    x0 = np.r_[z0, rho0.ravel()]
    def residual(x):
        pred = forward(points(x[:2]), alpha, poses)*scale @ x[2:].reshape(2,3)
        return ((pred-y)*weights).ravel()
    result = least_squares(residual, x0, bounds=([80,80]+[0]*6,[190,190]+[1]*6),
                           x_scale=[100,100]+[1]*6, max_nfev=150,
                           ftol=1e-10, xtol=1e-10, gtol=1e-9)
    return {'z_mm': result.x[:2].tolist(), 'rgb': result.x[2:].reshape(2,3).tolist(),
            'converged': bool(result.success), 'weighted_residual': float(2*result.cost),
            'grid_seed_mm': z0.tolist()}, objective


def depth_information(alpha, poses, scale):
    """Local Gaussian weighted Jacobian; profile 6 unknown band reflectances.

    This is a sensitivity diagnostic, not a guaranteed precision prediction.
    """
    f = forward(points(TRUE_Z), alpha, poses)*scale
    mu = f @ TRUE_RGB
    w = 1/np.sqrt(mu+READ_NOISE**2)
    jz = []
    for patch in range(2):
        zp, zm = TRUE_Z.copy(), TRUE_Z.copy()
        zp[patch] += .01
        zm[patch] -= .01
        d = ((forward(points(zp), alpha, poses)-forward(points(zm),alpha,poses))
             *scale/.02) @ TRUE_RGB
        jz.append((d*w).ravel())
    jr = []
    for patch in range(2):
        for band in range(3):
            col = np.zeros_like(mu)
            col[:,band] = f[:,patch]
            jr.append((col*w).ravel())
    jr, jz = np.array(jr).T, np.array(jz).T
    jprofile = jz-jr @ np.linalg.lstsq(jr,jz,rcond=None)[0]
    sv = np.linalg.svd(jprofile,compute_uv=False)
    cov = np.linalg.pinv(jprofile.T @ jprofile)
    return {'profiled_depth_singular_values_per_mm':sv.tolist(),
            'local_linear_std_mm':np.sqrt(np.diag(cov)).tolist()}


def validate_math():
    # Frontal sum at fixed footprint; facet normals, not narrow ray samples.
    checks = {}
    for alpha in [0.,30.,45.]:
        n = normals(alpha)
        area = BASE_AREA/(3*np.cos(np.deg2rad(alpha)))
        assert np.allclose(np.linalg.norm(n,axis=1),1)
        assert np.isclose(area*n[:,2].sum(),BASE_AREA)
        # A central beam and four off-axis beams with reweighted flux are
        # distinguishable incident fields but give identical three currents.
        t = np.deg2rad(20.)
        ring = np.array([[np.sin(t),0,np.cos(t)],[-np.sin(t),0,np.cos(t)],
                         [0,np.sin(t),np.cos(t)],[0,-np.sin(t),np.cos(t)]])
        axis = n @ [0.,0.,1.]
        mixed = (np.maximum(n @ ring.T,0)/(4*np.cos(t))).sum(axis=1)
        assert np.allclose(axis,mixed,rtol=1e-13,atol=1e-13)
        checks[str(alpha)] = {'normal_matrix_singular_values':np.linalg.svd(n,compute_uv=False).tolist(),
                             'angular_ambiguity_max_difference':float(np.max(np.abs(axis-mixed))),
                             'facet_area_mm2':float(area),
                             'height_mm':float(BASE/(2*np.sqrt(3))*np.tan(np.deg2rad(alpha)))}
    # Validate profile solver independently against bounded scipy solver.
    rng = np.random.default_rng(72)
    f0, f1, y = rng.uniform(.1,2,(12,3)),rng.uniform(.1,2,(12,4)),rng.uniform(-.2,4,(12,3))
    w = rng.uniform(.3,2,(12,3))
    calc = profiles(f0,f1,y,w)
    from scipy.optimize import lsq_linear
    ref = np.zeros((3,4))
    for i in range(3):
        for j in range(4):
            for band in range(3):
                m = np.c_[f0[:,i],f1[:,j]]*w[:,band,None]
                r = lsq_linear(m,y[:,band]*w[:,band],bounds=(0,1),tol=1e-12)
                ref[i,j] += 2*r.cost
    assert np.allclose(calc,ref,rtol=1e-9,atol=1e-9)
    checks['profile_solver_max_difference'] = float(np.max(np.abs(calc-ref)))
    # Independent closed-form check of the total flux in the all-front-facing
    # regime. Same projected receiver area, but tilted emitting facets direct
    # less of their fixed total optical energy toward this central scene.
    flat = forward(points(TRUE_Z),0.,MOVING).reshape(3,2,8,3,2).sum(axis=3)
    for alpha in [30.,45.]:
        tilted = forward(points(TRUE_Z),alpha,MOVING).reshape(3,2,8,3,2).sum(axis=3)
        assert np.allclose(tilted,flat*np.cos(np.deg2rad(alpha)),rtol=1e-12,atol=1e-30)
    checks['fixed_energy_total_flux_cosine_identity'] = True
    return checks


def main():
    started = time.perf_counter()
    checks = validate_math()
    # ONE calibration constant used by every geometry, pose and scene.
    # Reference: one on-axis white 1 mm2 patch at 150 mm, 0-degree detector.
    reference = forward([[0,0,150]],0.,STATIC)
    base_scale = 100_000 / (reference.sum()*3)
    rng = np.random.default_rng(260926)
    records = []
    for alpha, moving in CONFIGS:
        poses = MOVING if moving else STATIC
        for level in [1., .1]:
            scale = base_scale*level
            f = forward(points(TRUE_Z),alpha,poses)*scale
            mu = f @ TRUE_RGB
            grids = [forward(np.c_[np.tile(XY[p],(len(ZGRID),1)),ZGRID],alpha,poses)*scale
                     for p in range(2)]
            noiseless, objective = fit(mu,alpha,poses,scale,grids)
            assert np.max(np.abs(np.array(noiseless['z_mm'])-TRUE_Z)) < .001
            held_true = forward(points(TRUE_Z),alpha,HELD_OUT)*scale @ TRUE_RGB
            fits = []
            for trial in range(TRIALS):
                y = rng.poisson(mu).astype(float)+rng.normal(0,READ_NOISE,mu.shape)
                est,_ = fit(y,alpha,poses,scale,grids)
                held_pred = (forward(points(est['z_mm']),alpha,HELD_OUT)*scale
                             @ np.array(est['rgb']))
                est['held_out_relative_l2'] = float(np.linalg.norm(held_pred-held_true)/np.linalg.norm(held_true))
                fits.append(est)
            z = np.array([r['z_mm'] for r in fits])
            err = np.abs(z-TRUE_Z)
            # Fixed independent gain for each pixel facet across poses/slots.
            gain_rng = np.random.default_rng(814)
            gain_map = gain_rng.normal(1.,.01,(16,3))
            gain_slots = np.concatenate([gain_map[~PARITY].ravel(),gain_map[PARITY].ravel()])
            gains = np.tile(gain_slots,3)[:,None]
            mismatch,_ = fit(mu*gains,alpha,poses,scale,grids)
            row = {'tilt_deg':alpha, 'moving':moving, 'calibration_count_level':int(100000*level),
                   'expected_total_scene_electrons':float(mu.sum()),
                   'median_absolute_depth_error_each_patch_mm':np.median(err,axis=0).tolist(),
                   'median_mean_absolute_depth_error_mm':float(np.median(err.mean(axis=1))),
                   'p90_mean_absolute_depth_error_mm':float(np.quantile(err.mean(axis=1),.9)),
                   'trials_with_any_depth_error_over_10mm':int(np.sum(np.max(err,axis=1)>10)),
                   'boundary_trials':int(np.sum(np.any((z<80.01)|(z>189.99),axis=1))),
                   'median_rgb_absolute_error':float(np.median(np.abs(np.array([r['rgb'] for r in fits])-TRUE_RGB))),
                   'median_held_out_relative_l2':float(np.median([r['held_out_relative_l2'] for r in fits])),
                   'nonconverged_trials':int(sum(not r['converged'] for r in fits)),
                   'noiseless':noiseless,'gain_mismatch_1percent_no_random_noise':mismatch,
                   'local_information':depth_information(alpha,poses,scale),'trials':fits}
            records.append(row)
            print(json.dumps({k:v for k,v in row.items() if k not in ['trials','local_information','noiseless','gain_mismatch_1percent_no_random_noise']},ensure_ascii=False),flush=True)
            if alpha==45 and moving and level==1:
                np.savez_compressed(OUT/'measurements-45-moving.npz',expected=mu,training_design=f,
                                    held_out_expected=held_true,depth_grid=ZGRID,
                                    noiseless_profile=objective,example_noisy=y)
    result = {'status':'restricted synthetic inverse problem; no physical prototype',
              'assumptions':{'known_patch_xy_mm':XY.tolist(),'known_patch_area_mm2':1,
                             'known_normals':[0,0,-1],'truth_depth_mm':TRUE_Z.tolist(),
                             'truth_band_reflectances':TRUE_RGB.tolist(),'poses_static_mm':[p.tolist() for p in STATIC],
                             'poses_moving_mm':[p.tolist() for p in MOVING],'held_out_pose_mm':[0,20,0],
                             'tilts_from_panel_normal_deg':[0,30,45],'base_side_mm':BASE,
                             'footprint_base_area_mm2':float(BASE_AREA),'channels_per_band':144,
                             'spectral_bands':3,'total_readouts':432,'independent_noise_trials':TRIALS,
                             'search_depth_range_mm':[80,190],'search_step_mm':2,
                             'grid_followed_by_continuous_refinement':True,
                             'hypothetical_read_noise_electrons_rms':READ_NOISE,'seed':260926,
                             'shared_calibration_scale':float(base_scale)},
              'checks':checks,'configurations':records,'runtime_seconds':time.perf_counter()-started}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    plot(result)
    print(f'Wrote results and figures in {time.perf_counter()-started:.1f} s',flush=True)


def plot(result):
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes = plt.subplots(1,3,figsize=(15,4.7),layout='constrained')
    theta = np.linspace(-90,90,361)
    for alpha in [0,30,45]:
        axes[0].plot(theta,np.maximum(np.cos(np.deg2rad(theta-alpha)),0),label=f'Normal {alpha}°')
    axes[0].set(xlabel='Direction from panel normal (degrees)',ylabel='Relative cosine response',
                title='A facet receives a broad sector',ylim=(0,1.07))
    axes[0].legend(fontsize=9)
    for level,ax in zip([100000,10000],axes[1:]):
        selected=[r for r in result['configurations'] if r['calibration_count_level']==level]
        labels=[f"{r['tilt_deg']:.0f}°\n"+('moving' if r['moving'] else 'fixed') for r in selected]
        data=[np.abs(np.array([t['z_mm'] for t in r['trials']])-TRUE_Z).mean(axis=1) for r in selected]
        ax.boxplot(data,tick_labels=labels,showfliers=True)
        ax.set(ylabel='Mean absolute depth error / trial (mm)',
               title=f'Reference detected electrons: {level:,}')
        ax.tick_params(axis='x',labelsize=9)
    fig.suptitle('Synthetic two-patch example — known lateral positions, normals and areas',fontsize=15)
    for ext in ['png','svg']:
        fig.savefig(OUT/f'01-angle-and-depth.{ext}',dpi=160)
    plt.close(fig)
    chosen=next(r for r in result['configurations'] if r['tilt_deg']==45 and r['moving'] and r['calibration_count_level']==100000)
    z=np.array([r['z_mm'] for r in chosen['trials']])
    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for p,color in enumerate(['#a62b35','#386ca7']):
        axes[0].scatter(np.arange(TRIALS)+1,z[:,p],color=color,s=24,label=f'Patch {p+1} estimate')
        axes[0].axhline(TRUE_Z[p],color=color,linestyle='--',label=f'True depth {TRUE_Z[p]} mm')
    axes[0].set(xlabel='Independent noise trial',ylabel='Depth (mm)',title='45° facets + panel translation')
    axes[0].legend(fontsize=9)
    estimated=np.array([r['rgb'] for r in chosen['trials']])
    cols=['#d24b45','#3c9c6d','#477ac6']
    for p in range(2):
        x=np.arange(3)+p*4
        axes[1].bar(x-.16,TRUE_RGB[p],width=.3,color=cols,alpha=.35,label='True' if p==0 else None)
        axes[1].bar(x+.16,np.median(estimated[:,p,:],axis=0),width=.3,color=cols,
                    label='Median fitted' if p==0 else None)
    axes[1].set(xticks=[0,1,2,4,5,6],xticklabels=['R1','G1','B1','R2','G2','B2'],
                ylabel='Ideal calibrated band reflectance',ylim=(0,1),title='Colour coefficients, not an image')
    axes[1].legend()
    fig.suptitle('432 readings → 2 depths + 6 colour coefficients; all other scene parameters known',fontsize=13)
    for ext in ['png','svg']:
        fig.savefig(OUT/f'02-reconstruction.{ext}',dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
