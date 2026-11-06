"""Doc 32: parked 50-year storm with yaw lost, brake allowed to slip (K1 resistor closed). Aero torque margin shown by dividing the brake torque."""
import sys
from pathlib import Path; H=Path(__file__).parent; sys.path.insert(0,str(H)); sys.path.insert(0,str(H.parent/'loads'))
import numpy as np, sim6, dlc6, wind as W
res=[]
for brake,lab in ((1500,'1.5 kNm'),(1500/1.35,'1.5/1.35 (factored aero)'),(1500/1.6,'1.5/1.6')):
  for yaw,az in ((8,60),(0,0),(180,0)):
    tb=sim6.Turbine6(**dlc6.TB_KW, brake_torque=brake, brake_delay=0.0)
    f=dlc6.turbulent_field(55.0,0.11*55,T=300,dt=0.05,seed=700+az+yaw)
    sc=sim6.Scenario('slip',300,f,yaw=yaw,park_azimuth=az,rho=1.35,init_rpm=0.0,events={'estop_t':0.0})
    r=sim6.simulate6(tb,sc)
    m=r['t']>5
    rev=np.trapezoid(r['rpm'][m],r['t'][m])/60
    res.append(dict(brake=lab,brake_Nm=round(brake),yaw=yaw,azimuth=az,max_rpm=round(float(r['rpm'].max()),1),mean_rpm=round(float(r['rpm'][m].mean()),2),revs_300s=round(float(rev),1),Mflap_max_Nm=round(float(abs(r['Mflap0']).max()))))
    print(lab,yaw,az,'max rpm',round(r['rpm'].max(),1),'mean rpm',round(r['rpm'][m].mean(),2),'revs in 300 s',round(rev,1),'Mflap',round(abs(r['Mflap0']).max()))
import json
(H/'results'/'brake_hold6.json').write_text(json.dumps(res,indent=1))
