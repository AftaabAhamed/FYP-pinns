from typing import Union

from fastapi import FastAPI
import sqlite3
import pandas as pd
from fastapi.responses import JSONResponse

from task import ODEsim,RealSystem

from collections import deque

app = FastAPI()

from task import TransferFunctionModel

# Database file path
DB_PATH = "history.db"

"""-----------------ODE----------------"""

ODE_ht = deque([(0,0),(0,0)])
# stopsim = False
ode = ODEsim(ode_height=ODE_ht,stop_sim=True, setpoint=0.1)

@app.get("/ODE/")
def start_ODE():
    
    if not ode.stop_sim:
        return {"status": "already running"}

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

rs = RealSystem(real_height=real_ht,stop_sim=True ,setpoint=0.1)

@app.get("/real/")
def start_real(setpoint : float):
    # if setpoint is not None:
    #     rs.setpoint = setpoint
    if not rs.stop_sim:
        return {"status": "already running"}
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


tfm = TransferFunctionModel(height_queue=tf_ht, stop_sim=True, setpoint=0.1)

@app.get("/tfm/")
def start_tfm(setpoint: float = None):

    if not tfm.stop_sim:
        return {"status": "already running"}

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

@app.get("/history/{model_name}")
def get_history(model_name: str):
    """
    Fetch historical data (time, height, voltage) from the database for a given model.

    Args:
        model_name (str): The name of the model (e.g., "ODEsim", "RealSystem", "TransferFunctionModel").

    Returns:
        JSONResponse: A JSON object containing the historical data.
    """
    # Validate model name
    valid_models = ["ODEsim", "RealSystem", "TransferFunctionModel"]
    if model_name not in valid_models:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid model name. Choose from {valid_models}."},
        )

    # Connect to the database
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT time, height, voltage FROM {model_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Convert the DataFrame to a list of dictionaries
        data = df.to_dict(orient="records")
        return {"model": model_name, "data": data}

    except sqlite3.Error as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Database error: {e}"},
        )