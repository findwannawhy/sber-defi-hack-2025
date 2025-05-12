import os
import uuid
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from app.core.config import settings

# --- Константы ---
TEMP_HTML_DIR = Path(__file__).parent / "temp_visualisation_html"
FRONTEND_BASE_URL = settings.FRONTEND_BASE_URL

# Создаем директорию, если она не существует
try:
    os.makedirs(TEMP_HTML_DIR, exist_ok=True)
except Exception as e:
    raise RuntimeError(f"Не удалось создать директорию для визуализаций: {str(e)}")

# --- Модели Pydantic ---
class VisualiseRequest(BaseModel):
    network: str = Field(..., description="Сеть контракта (например, 'mainnet', 'base', 'arbitrum')")
    address: str = Field(..., description="Адрес контракта")
    source: Literal['bot', 'web'] = Field(..., description="Источник запроса ('bot' или 'web')")

class VisualiseResponse(BaseModel):
    url: str = Field(..., description="URL для просмотра визуализации на фронтенде")


def generate_and_save_html(network: str, address: str, visualization_id: str) -> Path:
    file_path = TEMP_HTML_DIR / f"{visualization_id}.html"

    html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Визуализация Контракта</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; }}
                .info {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Визуализация для контракта</h1>
            <div class="info">
                <p><span class="label">Сеть:</span> {network}</p>
                <p><span class="label">Адрес:</span> {address}</p>
                <p><span class="label">ID Визуализации:</span> {visualization_id}</p>
                <p><em>(Здесь должна быть ваша реальная визуализация)</em></p>
            </div>
        </body>
        </html>
        """

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить файл визуализации: {str(e)}")

router = APIRouter()

@router.post("/run")
async def run_visualise(request_data: VisualiseRequest = Body(...)):

    visualization_id = str(uuid.uuid4())
    try:
        html_file_path = generate_and_save_html(
            network=request_data.network,
            address=request_data.address,
            visualization_id=visualization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при создании визуализации")

    if request_data.source == 'bot':
        frontend_url = f"{FRONTEND_BASE_URL}/proxy-visualisation/{visualization_id}"
        return VisualiseResponse(url=frontend_url)

    elif request_data.source == 'web':
        try:
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            filename = f"{visualization_id}.html"
            return HTMLResponse(
                content=html_content,
                headers={"X-Filename": filename}
            )
        except IOError as e:
            raise HTTPException(status_code=500, detail="Не удалось прочитать файл визуализации")
    else:
        raise HTTPException(status_code=400, detail="Некорректный источник запроса")


@router.get("/html/{visualization_id}", response_class=FileResponse)
async def get_visualisation_html(visualization_id: str):
    try:
        uuid.UUID(visualization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный ID визуализации")

    file_path = TEMP_HTML_DIR / f"{visualization_id}.html"

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Визуализация не найдена")

    return FileResponse(path=file_path, media_type="text/html")