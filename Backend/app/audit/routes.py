from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from app.schemas import ContractCreate, AuditReport
from datetime import datetime
import os
import logging
from fpdf import FPDF
from pathlib import Path
from dotenv import load_dotenv
from app.audit.data_analys import compile_solidity_files
from app.audit.model_analys import get_analys
import numpy as np

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Определяем базовую директорию относительно текущего файла
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "temp_pdfs"
FONTS_DIR = BASE_DIR / "fonts"

# Убедимся, что директория шрифтов существует и доступна
if not FONTS_DIR.is_dir():
    # Попытка создать директорию, если её нет (хотя обычно она должна быть частью репозитория)
    try:
        os.makedirs(FONTS_DIR, exist_ok=True)
        logger.warning(f"Fonts directory was missing, created: {FONTS_DIR}")
    except OSError as e:
        logger.error(f"Could not create fonts directory {FONTS_DIR}: {e}")
        # Можно выбросить исключение или продолжить без пользовательских шрифтов
        # raise HTTPException(status_code=500, detail="Fonts directory missing or inaccessible")

# Проверка существования файлов шрифтов перед их использованием
dejavu_regular_path = FONTS_DIR / 'DejaVuSansCondensed.ttf'
dejavu_bold_path = FONTS_DIR / 'DejaVuSansCondensed-Bold.ttf'
# Удаляем проверку для моноширинных шрифтов
# dejavu_mono_regular_path = FONTS_DIR / 'DejaVuSansMono.ttf'
# dejavu_mono_bold_path = FONTS_DIR / 'DejaVuSansMono-Bold.ttf'

required_fonts = {
    "DejaVu": dejavu_regular_path,
    "DejaVuB": dejavu_bold_path,
    # Удаляем моноширинные шрифты из проверки
    # "DejaVuMono": dejavu_mono_regular_path,
    # "DejaVuMonoB": dejavu_mono_bold_path,
}

missing_fonts = []
for name, path in required_fonts.items():
    if not path.is_file():
        missing_fonts.append(str(path))

if missing_fonts:
    logger.error(f"Missing required font files: {', '.join(missing_fonts)}")
    raise HTTPException(status_code=500, detail=f"Missing required font files needed for PDF generation: {', '.join(missing_fonts)}")

# Функция для удаления файла в фоновом режиме
async def remove_file(path: str) -> None:
    try:
        os.remove(path)
        logger.info(f"Successfully removed temporary file: {path}")
    except FileNotFoundError:
        logger.warning(f"Temporary file not found, could not remove: {path}")
    except Exception as e:
        logger.error(f"Error removing temporary file {path}: {e}")

def format_analysis_results(all_model_predictions):
    if not all_model_predictions:
        return "Анализ не был выполнен."
    
    formatted_text = ""
    for model_name, output in all_model_predictions.items():
        formatted_text += f"\nМодель: {model_name.split('.')[0]}\n"
        
        predictions = output.get('predictions')
        probabilities = output.get('probabilities')
        
        # Обработка предсказаний
        if isinstance(predictions, (list, np.ndarray)):
            pred_text = ", ".join(map(str, predictions.tolist() if isinstance(predictions, np.ndarray) else predictions))
        else:
            pred_text = str(predictions)
        
        pred_description = ""
            
        if int(pred_text) == 0:
            pred_description = "Есть уязвимости"
        elif int(pred_text) == 1:
            pred_description = "Нет уязвимостей"
            
        formatted_text += f"Предсказание: {pred_description}\n"
        
        # Обработка вероятностей
        if isinstance(probabilities, (list, np.ndarray)):
            if isinstance(probabilities, np.ndarray):
                probabilities = probabilities.tolist()
            
            # Обработка вложенных списков
            if probabilities and isinstance(probabilities[0], (list, np.ndarray)):
                prob_texts = []
                for prob_list in probabilities:
                    if isinstance(prob_list, np.ndarray):
                        prob_list = prob_list.tolist()
                    prob_texts.append(", ".join([f"{float(p):.2f}" for p in prob_list]))
                prob_text = " | ".join(prob_texts)
            else:
                prob_text = ", ".join([f"{float(p):.2f}" for p in probabilities])
                
            formatted_text += f"Уверенность модели: {float(probabilities[0][int(pred_text)]):.2%}\n"
        elif probabilities != "N/A":
            formatted_text += f"Уверенность: {probabilities}\n"
            
        formatted_text += "-" * 40 + "\n"
    
    return formatted_text

@router.post("/run")
async def run_audit(
    request_data: ContractCreate,
):
    logger.info(f"Received run request for contract {request_data.address} on network {request_data.network}")

    findings = compile_solidity_files(request_data.address, request_data.network)
    try:
        all_model_predictions = get_analys(request_data.address, request_data.network)
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        all_model_predictions = {}
        
    # 2. Формируем данные для отчета (пример)
    report_data = AuditReport(
        contract_address=request_data.address,
        network=request_data.network,
        audit_timestamp=datetime.utcnow(),
        findings=["Потенциальное reentrancy vulnerability"],
        summary="Basic audit completed. Found potential issues."
    )

    # 3. Генерируем PDF с помощью fpdf2
    pdf_filename = f"audit_{request_data.address}_{request_data.network}.pdf"

    # Убедимся, что директория существует прямо перед использованием
    try:
        os.makedirs(PDF_DIR, exist_ok=True)
        logger.info(f"Ensured PDF directory exists: {PDF_DIR}")
    except OSError as e:
        logger.error(f"Could not create PDF directory {PDF_DIR}: {e}")
        # Обработка ошибки создания директории (например, возврат ошибки 500)
        raise HTTPException(status_code=500, detail="Failed to create PDF directory")

    pdf_path = PDF_DIR / pdf_filename # Используем pathlib для формирования пути

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12) # Базовый шрифт, если DejaVu не загрузится

    # Используем абсолютные пути к шрифтам (уже проверенные)
    try:
        pdf.add_font('DejaVu', '', str(dejavu_regular_path), uni=True) # шрифт DejaVu
        pdf.add_font('DejaVu', 'B', str(dejavu_bold_path), uni=True) # жирная версия
        # Удаляем добавление моноширинных шрифтов
        # pdf.add_font('DejaVuMono', '', str(dejavu_mono_regular_path), uni=True) # моноширинный шрифт
        # pdf.add_font('DejaVuMono', 'B', str(dejavu_mono_bold_path), uni=True) # моноширинный жирный
        pdf.set_font('DejaVu', '', 12)
        logger.info("Successfully loaded DejaVu fonts.")
    except RuntimeError as e:
        logger.error(f"Failed to load fonts: {e}. Using default font.")
        pdf.set_font("Arial", size=12) # Возврат к базовому шрифту при ошибке

    pdf.set_font("DejaVu", 'B', size=16) # Крупный заголовок
    pdf.cell(0, 10, txt=f"Audit Report for {report_data.contract_address}", ln=1, align="C")
    pdf.ln(5) # Отступ поменьше

    pdf.set_font("DejaVu", '', size=11)
    pdf.cell(0, 8, txt=f"Network: {report_data.network}", ln=1)
    pdf.ln(10) # Добавляем отступ

    pdf.set_font("DejaVu", 'B', size=14) # Используем DejaVu Bold
    pdf.cell(0, 10, txt="Наш анализ:", ln=1)
    pdf.set_font("DejaVu", size=11) # Используем DejaVu, чуть меньше
    formatted_analysis = format_analysis_results(all_model_predictions)
    pdf.multi_cell(0, 6, txt=formatted_analysis, align="L")

    pdf.ln(10) # Добавляем отступ перед новым разделом

    pdf.set_font("DejaVu", 'B', size=14) # Используем DejaVu Bold
    pdf.cell(0, 10, txt="Слабые места:", ln=1)
    pdf.ln(5) # Добавляем отступ перед списком уязвимостей

    # Проходим по списку найденных уязвимостей (словари)
    for finding in findings:
        print(finding) # Оставляем для отладки
        # Название уязвимости - жирным
        pdf.set_font("DejaVu", 'B', size=12)
        pdf.cell(0, 6, txt=f"Уязвимость: {finding.get('vulnerability', 'N/A')}", ln=1)

        # Остальные детали - обычным шрифтом, чуть меньше
        pdf.set_font("DejaVu", '', size=10)
        left_indent = 10 # Отступ для полей
        field_line_height = 5

        # Выводим детали с отступом
        pdf.cell(left_indent) # Небольшой отступ слева
        pdf.cell(0, field_line_height, txt=f"Уверенность: {finding.get('confidence', 'N/A')}", ln=1)

        pdf.cell(left_indent) # Небольшой отступ слева
        pdf.cell(0, field_line_height, txt=f"Влияние: {finding.get('impact', 'N/A')}", ln=1)

        # Описание может быть длинным
        description = finding.get('description')
        pdf.cell(left_indent) # Отступ для описания
        if description:
            pdf.multi_cell(0, field_line_height, txt=f"{description}", align="L") # Ширина 0 - до правого края
        else:
            pdf.cell(0, field_line_height, txt="Описание: N/A", ln=1)
        pdf.ln(2) # Небольшой отступ после описания

        # Фрагмент кода
        code_snippet = finding.get('function_lines')
        if code_snippet:
            # --- Расчет высоты блока кода и проверка на разрыв страницы ---
            code_font_size = 9
            line_height = 4 # Высота строки для шрифта
            code_padding = 3 # Отступы внутри рамки
            left_indent = 10 # Отступ слева для блока
            available_width = pdf.w - pdf.l_margin - pdf.r_margin - left_indent # Ширина доступная для блока кода

            # Предварительно устанавливаем шрифт, чтобы правильно измерить текст
            pdf.set_font("DejaVu", '', code_font_size) # Используем обычный шрифт для расчета, т.к. он не моноширинный

            # Расчет высоты блока кода
            try:
                split_lines = pdf.multi_cell(
                    w=available_width - 2 * code_padding,
                    h=line_height,
                    txt=code_snippet.strip(),
                    align="L",
                    dry_run=True,
                    output="LINES"
                )
                num_lines_actual = len(split_lines) if split_lines else 1
                code_block_height = num_lines_actual * line_height + 2 * code_padding
            except TypeError:
                logger.warning("multi_cell dry_run might not be supported or failed; falling back to estimation.")
                num_lines_estimated = code_snippet.strip().count('\n') + 1
                # TODO: Улучшить запасной расчет
                code_block_height = num_lines_estimated * line_height + 2 * code_padding

            # Высота заголовка "Фрагмент кода..." + отступы до и после него
            title_height = 5 # Высота cell для заголовка
            space_before_title = 0 # pdf.ln(2) перед заголовком уже сделан ранее
            space_after_title = 2 # pdf.ln(2) после заголовка
            space_after_block = 2 # pdf.ln(2) после блока кода

            total_block_height_needed = space_before_title + title_height + space_after_title + code_block_height + space_after_block

            # Проверяем, помещается ли блок на текущей странице
            available_page_space = pdf.h - pdf.b_margin - pdf.get_y()
            if total_block_height_needed > available_page_space:
                pdf.add_page()
                # Сбрасываем y координату после добавления страницы, если нужно
                # start_y = pdf.t_margin # Или другое значение, если отступ сверху нужен другой
            # --- Конец расчета и проверки на разрыв страницы ---

            # Теперь рисуем сам блок
            pdf.cell(left_indent) # Отступ для заголовка кода
            pdf.set_font("DejaVu", '', size=10) # Шрифт для заголовка блока кода
            pdf.cell(0, title_height, txt="Фрагмент кода из контракта, помеченный как уязвимый:", ln=1)
            pdf.ln(space_after_title) # Маленький отступ после заголовка

            # --- Начало блока форматирования кода ---
            rect_indent = pdf.l_margin + left_indent # Отступ слева как у остального текста

            # Позиция перед отрисовкой блока
            start_x = rect_indent
            start_y = pdf.get_y()

            # Устанавливаем шрифт для кода (возвращаем DejaVu)
            pdf.set_font("DejaVu", '', code_font_size)

            # Отрисовка фона и рамки
            pdf.set_fill_color(245, 245, 245) # Очень светло-серый фон
            pdf.set_draw_color(220, 220, 220) # Светло-серая рамка
            pdf.set_line_width(0.2)
            # Используем уже рассчитанную code_block_height
            pdf.rect(start_x, start_y, available_width, code_block_height, style='FD') # FD = Fill and Draw

            # Устанавливаем курсор внутрь рамки с отступом
            pdf.set_xy(start_x + code_padding, start_y + code_padding)

            # Выводим сам код с шрифтом DejaVu
            pdf.multi_cell(
                w=available_width - 2 * code_padding,
                h=line_height,
                txt=code_snippet.strip(),
                align="L",
                border=0 # Рамку мы нарисовали отдельно
            )

            # Устанавливаем Y координату после блока, чтобы pdf.ln() работал корректно
            pdf.set_y(start_y + code_block_height)

            pdf.ln(space_after_block) # Небольшой отступ после блока кода

            # --- Конец блока форматирования кода ---

            pdf.set_font("DejaVu", '', size=10) # Возвращаем обычный шрифт и размер
        else:
            pdf.cell(left_indent)
            pdf.cell(0, 5, txt="Фрагмент кода: N/A", ln=1)

        pdf.ln(10) # Увеличиваем отступ между записями об уязвимостях

    try:
        pdf.output(str(pdf_path), "F") # Сохраняем PDF в файл, передавая путь как строку
        logger.info(f"Generated PDF report at: {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        # Обработка ошибки генерации PDF (например, возврат ошибки 500)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    # 4. Возвращаем PDF как FileResponse с фоновой задачей для удаления
    return FileResponse(
        path=pdf_path,
        filename=pdf_filename,
        media_type='application/pdf',
        # TODO: Раскомментировать функцию удаления файла после отправки
        # background=BackgroundTask(remove_file, path=pdf_path)
    )