import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any

from function.func_ocr import PaddleOCRManager
from function.func_connection import ConnectionManager

ocr_manager = PaddleOCRManager()
conn_manager = ConnectionManager()

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
    # 7. uvicorn 서버를 사용하여 앱을 실행합니다.
    #    다른 PC(Java가 실행되는 PC)에서 접근 가능하도록 host='0.0.0.0'으로 설정합니다.
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
