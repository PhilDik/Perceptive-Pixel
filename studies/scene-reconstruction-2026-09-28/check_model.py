"""Independent derivative, rigid-transform, quadrature and radiometry checks."""
from pathlib import Path
import json
import numpy as np
import scene_model as s
ROOT=Path(__file__).resolve().parent

def main():
    points=np.array([[-24.3,-12.8,48.6],[7.2,18.4,77.3],[27.6,-5.1,111.8]])
    scale=s.calibration();panel=s.make_panel(15);seq=s.poses('rigid')
    a=s.Acquisition(panel,seq,n=2,scale=scale);F,J=a.forward(points,derivative=True)
    errors=[]
    for j in range(3):
        for axis in range(3):
            delta=np.zeros_like(points);delta[j,axis]=1e-4
            numeric=(a.forward(points+delta)-a.forward(points-delta))/(2e-4)
            errors.append(float(np.linalg.norm(numeric[:,j]-J[:,j,axis])/np.linalg.norm(numeric[:,j])))
    Q=s.rotation(23,-17);translation=np.array([43.,-12.,31.])
    transformed=s.Acquisition(panel,[(Q@R,Q@t+translation) for R,t in seq],n=2,scale=scale)
    rigid=transformed.forward(points@Q.T+translation,np.tile(s.NORM@Q.T,(3,1)))
    invariant=float(np.linalg.norm(rigid-F)/np.linalg.norm(F))
    quadrature={}
    previous=None
    for n in [1,2,4,8]:
        ff=s.Acquisition(panel,seq,n=n,scale=scale).forward(points)
        if previous is not None:quadrature[f'{n//2}_to_{n}']=float(np.linalg.norm(ff-previous)/np.linalg.norm(ff))
        previous=ff
    shadow=s.Acquisition(panel,seq,n=4,scale=scale).shadow_fraction(points)
    exchange=panel.exchange(4)
    bg=a.background(exchange,1e-6).reshape(5,-1)
    assert np.allclose(bg,bg[:1])
    assert max(errors)<1e-6 and invariant<1e-12
    # Independent far-axis point approximation for a flat panel: 1/r^4 transport.
    flat=s.Acquisition(s.make_panel(0),s.poses('static'),n=4,scale=scale)
    far=flat.forward([[0,0,10000.],[0,0,20000.]]).sum(axis=0)
    distance_ratio=float(far[0]/far[1])
    assert abs(distance_ratio-16)<.002
    out={'analytic_xyz_jacobian_max_relative_error':max(errors),'joint_rigid_transform_relative_error':invariant,
      'quadrature_relative_l2':quadrature,'checked_scene_shadow_fraction':shadow,'background_pose_invariant':True,
      'far_point_signal_ratio_10m_to_20m':distance_ratio,'energy_exchange_max_row_sum':float(exchange.sum(axis=1).max()),
      'known_limits':'Selected configurations only; geometric optics and Lambertian point-patch assumption; no hardware validation.'}
    (ROOT/'model-checks.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))

if __name__=='__main__':main()
