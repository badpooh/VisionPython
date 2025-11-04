import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time
import os
from datetime import datetime
import threading

from function.func_ocr import PaddleOCRManager
from function.func_connection import ConnectionManager
from function.func_modbus import ModbusLabels
from demo_test.demo_process import DemoTest
from function.func_process import Canceled, CancelToken

demo_test = DemoTest()

ocr_manager = PaddleOCRManager()
conn_manager = ConnectionManager()
modbus_manager = ModbusLabels()

_cancel = CancelToken()
_worker: Optional[threading.Thread] = None
_lock = threading.Lock()
_last_status = {"running": False, "message": "idle"}

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

class ConnectionRequest(BaseModel):
    ip_address: str = Field(alias="ip")
    touch_port: int
    setup_port: int

    class Config:
        populate_by_name = True

class DisconnectionRequest(BaseModel):
    message: str

class InitializationRequest(BaseModel):
    message: str

class TestProcess(BaseModel):
    message: str

@app.post("/connect")
async def connect_modbus(request: ConnectionRequest):
    try:
        conn_manager.ip_connect(request.ip_address)
        conn_manager.tp_update(request.touch_port)
        conn_manager.sp_update(request.setup_port)
        conn_manager.start_monitoring()
        if conn_manager.is_connected:
            return {"status": "success", "message": "Modbus TCP connected and monitoring started."}
        else:
            raise HTTPException(status_code=500, detail="Failed to establish Modbus TCP connection.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect")
async def disconnect_modbus():
    try:
        conn_manager.tcp_disconnect()
        return {"status": "success", "message": "Modbus TCP disconnected."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Initialize")
async def initialize_modbus(request: InitializationRequest):
    try:
        if conn_manager.is_connected:
            modbus_manager.setup_initialization()
        else:
            raise HTTPException(status_code=500, detail="Modbus TCP is not connected.")
        return {"status": "success", "message": "Modbus TCP initialized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test_mode_balance")
def modbus_test_mode_balance(request: TestProcess):

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_save_path = os.path.expanduser(f"./results/{current_time}/")
    os.makedirs(base_save_path, exist_ok=True)
    ip = conn_manager.SERVER_IP

    image_directory = f"//10.10.20.30/screenshot/{ip}"
    search_pattern = os.path.join(image_directory, '**/*.png')

    print(f"[PATH] base_save_path set to: {base_save_path}")
    print(f"[PATH] search_pattern set to: {search_pattern}")
    try:
        if conn_manager.is_connected:
            demo_test.clear_cancel_flag()
            modbus_manager.test_mode_balance_setting()
            time.sleep(1)
            demo_test.meter_test_mode_balance(base_save_path, search_pattern)
        else:
            raise HTTPException(status_code=500, detail="Modbus TCP is not connected.")
        return {"status": "success", "message": "Modbus TCP initialized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/stop_test")
def stop_current_test():
    """
    현재 실행 중인 demo_test 작업을 중단하도록 신호를 보냅니다.
    """
    try:
        demo_test.cancel_test()
        return {"status": "success", "message": "Test cancellation signal sent."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
