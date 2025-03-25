from typing import Union

from fastapi import FastAPI

from task import ODEsim,RealSystem

from collections import deque

app = FastAPI()

import sqlite3
from task import TransferFunctionModel

"""-----------------ODE----------------"""

ODE_ht = deque([(0,0),(0,0)])
# stopsim = False
ode = ODEsim(ode_height=ODE_ht,stop_sim=False, setpoint=0.1)

@app.get("/ODE/")
def start_ODE():
    # if not ode.stop_sim:
    #     return {"status": "already running"}

    status = ode.start()
    return {"status": status}

@app.get("/ODE/data")
def get_ht_ODE():    
    return {"height": ODE_ht[-1][0],"time":ODE_ht[-1][1]}


@app.get("/ODE/status")
def get_status_ODE():
    
    kp = ode.Kp
    ki = ode.Ki
    kd = ode.Kd
    
    vin = ode.vin
    setpoint = ode.setpoint
    ctrlr_mode = "openloop" if ode.is_openloop else "closedloop"

    running = not ode.stop_sim

    return {"Kp": kp, "Ki": ki, "Kd": kd, "Vin": vin, "Setpoint": setpoint, "ctrlr_mode": ctrlr_mode, "running": running}


@app.post("/ODE/update_setpoint")
def update_setpoint_ODE(setpoint: float):
    ode.update_setpoint(setpoint)
    return {"message": f"Setpoint updated to {setpoint}"}

@app.post("/ODE/is_openloop")
def is_openloop_ODE(is_openloop: bool):
    ode.is_openloop = is_openloop
    return {"message": f"Openloop status updated to {is_openloop}"}

@app.post("/ODE/update_ctrlr")
def update_ctrlr_ODE(Kp: float, Ki: float, Kd: float):
    ode.update_ctrlr(Kp, Ki, Kd)
    return {"message": f"Controller updated to {Kp, Ki, Kd}"}

@app.post("/ODE/update_vin")
def update_vin_ODE(vin: float):
    ode.vin = vin
    return {"message": f"Vin updated to {vin}"}

@app.post("/ODE/stop")
def stop_ODE():
    ode.stop()
    return {"message": "ODE simulation stopped"}



"""------------Real System-------------"""



real_ht = deque([(0,0),(0,0)])

rs = RealSystem(real_height=real_ht,stop_sim=False,setpoint=0.1)

@app.get("/real/")
def start_real(setpoint : float):
    if setpoint is not None:
        rs.setpoint = setpoint
    status = rs.start()
    return {"status": status}

@app.get("/real/data")
def get_ht_real():
    return {"height": real_ht[-1][0], "time": real_ht[-1][1]}

@app.get("/real/status")
def get_status_real():
    
    kp = rs.Kp
    ki = rs.Ki
    kd = rs.Kd
    
    vin = rs.vin
    setpoint = rs.setpoint
    ctrlr_mode = "openloop" if rs.is_openloop else "closedloop"

    running = not rs.stop_sim

    return {"Kp": kp, "Ki": ki, "Kd": kd, "Vin": vin, "Setpoint": setpoint, "ctrlr_mode": ctrlr_mode, "running": running}

@app.post("/real/update_setpoint")
def update_setpoint_real(setpoint: float):
    rs.update_setpoint(setpoint)
    return {"message": f"Setpoint updated to {setpoint}"}

@app.post("/real/is_openloop")
def is_openloop_real(is_openloop: bool):
    rs.is_openloop = is_openloop
    return {"message": f"Openloop status updated to {is_openloop}"}

@app.post("/real/update_ctrlr")
def update_ctrlr_real(Kp: float, Ki: float, Kd: float):
    rs.update_ctrlr(Kp, Ki, Kd)
    return {"message": f"Controller updated to {Kp, Ki, Kd}"}

@app.post("/real/update_vin")
def update_vin_real(vin: float):
    rs.vin = vin
    return {"message": f"Vin updated to {vin}"}

@app.post("/real/stop")
def stop_real():
    rs.stop()
    return {"message": "Real system simulation stopped"}



"""------------Transfer Function Model-------------"""

tf_ht = deque([(0, 0), (0, 0)])


tfm = TransferFunctionModel(height_queue=tf_ht, stop_sim=False, setpoint=0.1)

@app.get("/tfm/")
def start_tfm(setpoint: float = None):
    if setpoint is not None:
        tfm.setpoint = setpoint
    status = tfm.start()
    return {"status": status}

@app.get("/tfm/data")
def get_ht_tfm():
    return {"height": tf_ht[-1][0], "time": tf_ht[-1][1]}

@app.get("/tfm/status")
def get_status_tfm():
    kp = tfm.Kp
    ki = tfm.Ki
    kd = tfm.Kd

    vin = tfm.vin
    setpoint = tfm.setpoint
    ctrlr_mode = "openloop" if tfm.is_openloop else "closedloop"

    running = not tfm.stop_sim

    return {"Kp": kp, "Ki": ki, "Kd": kd, "Vin": vin, "Setpoint": setpoint, "ctrlr_mode": ctrlr_mode, "running": running}

@app.post("/tfm/update_setpoint")
def update_setpoint_tfm(setpoint: float):
    tfm.update_setpoint(setpoint)
    return {"message": f"Setpoint updated to {setpoint}"}

@app.post("/tfm/is_openloop")
def is_openloop_tfm(is_openloop: bool):
    tfm.is_openloop = is_openloop
    return {"message": f"Openloop status updated to {is_openloop}"}

@app.post("/tfm/update_ctrlr")
def update_ctrlr_tfm(Kp: float, Ki: float, Kd: float):
    tfm.update_ctrlr(Kp, Ki, Kd)
    return {"message": f"Controller updated to {Kp, Ki, Kd}"}

@app.post("/tfm/update_vin")
def update_vin_tfm(vin: float):
    tfm.vin = vin
    return {"message": f"Vin updated to {vin}"}

@app.post("/tfm/stop")
def stop_tfm():
    tfm.stop()
    return {"message": "Transfer function model simulation stopped"}

"""------------ general -------------"""
@app.post("/schedule/")
def schedule(schedule : list):
    ode.schedule.extend(schedule)
    # rs.schedule = rs.schedule + schedule

    return {"message": "Scheduled"}