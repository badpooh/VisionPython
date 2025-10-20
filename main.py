import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any

from function.func_ocr import PaddleOCRManager

ocr_manager = PaddleOCRManager()

app = FastAPI()

# 2. 요청 본문(Request Body)의 데이터 구조를 정의합니다.
#    Java가 보내줄 JSON의 형식을 미리 알려주는 역할을 합니다.
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
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
