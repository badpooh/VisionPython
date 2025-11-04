import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any
import time
import os
from datetime import datetime

from function.func_ocr import PaddleOCRManager
from function.func_connection import ConnectionManager
from function.func_modbus import ModbusLabels
from demo_test.demo_process import DemoTest

demo_test = DemoTest()

ocr_manager = PaddleOCRManager()
conn_manager = ConnectionManager()
modbus_manager = ModbusLabels()

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
    
class InitializationRequest(BaseModel):
    message: str

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
    
class TestProcess(BaseModel):
    message: str


@app.post("/test_mode_balance")
async def modbus_test_mode_balance(request: TestProcess):

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
            modbus_manager.test_mode_balance_setting()
            time.sleep(1)
            demo_test.meter_test_mode_balance(base_save_path, search_pattern)
        else:
            raise HTTPException(status_code=500, detail="Modbus TCP is not connected.")
        return {"status": "success", "message": "Modbus TCP initialized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OcrRequest(BaseModel):
    image_path: str
    roi_keys: List[Any]

# 3. POST 요청을 처리할 API 엔드포인트를 정의합니다.
@app.post("/ocr")
async def ocr_endpoint(request_data: OcrRequest):
    """
    Java로부터 이미지 경로와 ROI 정보를 받아 OCR을 수행하고 결과를 반환합니다.
    """
    try:
        # 4. Pydantic 모델 덕분에 데이터가 자동으로 검증되고 객체로 변환됩니다.
        #    이제 request_data.image_path 처럼 직접 속성에 접근할 수 있습니다.
        ocr_results = ocr_manager.paddleocr_basic(request_data.image_path, request_data.roi_keys)
        
        # 5. 결과를 딕셔너리 형태로 반환하면 FastAPI가 자동으로 JSON으로 변환해줍니다.
        return {"status": "success", "results": ocr_results}
    except Exception as e:
        # 6. 에러가 발생하면 표준 HTTP 에러를 발생시킵니다.
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
