"""SEE PRO multi-format evidence intake (read-only, session-only).

Never writes to Drive/Sheets or external AI services. OCR is unverified.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
import re
from tdv_real_intake import extract_document, candidate_lots, MAX_UPLOAD, MAX_ROWS

IMAGES = {"png", "jpg", "jpeg", "tif", "tiff"}
ACCEPTED = ("pdf", "docx", "xlsx", "xls", "csv", "png", "jpg", "jpeg", "tif", "tiff")


def _image_ocr(data: bytes) -> tuple[str, int]:
    """Local Vietnamese/English OCR at 0/90/180/270 degrees; choose best confidence."""
    from PIL import Image, ImageOps
    import pytesseract
    from pytesseract import Output

    image = ImageOps.exif_transpose(Image.open(BytesIO(data)))
    if getattr(image, "n_frames", 1) != 1:
        raise ValueError("TIFF nhiều trang: chưa hỗ trợ đọc đủ tất cả các khung ảnh")
    if image.width * image.height > 12_000_000:
        raise ValueError("Ảnh quá 12 megapixel; cần chia ảnh để OCR an toàn")
    if max(image.size) > 2200:
        ratio = 2200 / max(image.size)
        image = image.resize((max(1, int(image.width * ratio)),
                              max(1, int(image.height * ratio))))
    image = image.convert("RGB")
    best = ("", -1.0, 0)
    for angle in (0, 90, 180, 270):
        frame = image.rotate(angle, expand=True) if angle else image
        try:
            data_out = pytesseract.image_to_data(
                frame, lang="vie+eng", config="--psm 6", output_type=Output.DICT)
        except (pytesseract.TesseractError, OSError) as exc:
            raise RuntimeError("OCR cục bộ không khả dụng; cần đối chiếu ảnh gốc") from exc
        tokens = []
        for token, confidence in zip(data_out.get("text", []), data_out.get("conf", [])):
            token = str(token).strip()
            try:
                conf = float(confidence)
            except (ValueError, TypeError):
                conf = -1
            if token and conf >= 20:
                tokens.append((token, conf))
        score = sum(c for _, c in tokens) / max(1, len(tokens))
        if tokens and (score > best[1] or (score == best[1] and len(tokens) > len(best[0]))):
            best = (" ".join(t for t, _ in tokens), score, angle)
    return best[0], best[2]


def extract_file(filename: str, data: bytes, *, ocr: bool = False) -> dict:
    """Extract evidence from PDF, Word, Excel, CSV, or photos.

    Preserve provenance, document SHA and uncertainty; no bidding decisions.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ACCEPTED:
        raise ValueError("Định dạng không hỗ trợ")
    if not data or len(data) > MAX_UPLOAD:
        raise ValueError("Tệp rỗng hoặc vượt giới hạn 30 MB")
    if ext in IMAGES:
        result = {"name": filename, "sha256": hashlib.sha256(data).hexdigest(),
                  "type": ext, "lines": [], "warnings": [], "pages": 1,
                  "complete": False, "verified": False}
        if ocr:
            text, rotation = _image_ocr(data)
            result["lines"] = [{"source": f"Ảnh OCR xoay {rotation}°", "text": line[:2500]}
                               for line in text.splitlines() if line.strip()]
            if not result["lines"] and text.strip():
                result["lines"] = [{"source": f"Ảnh OCR xoay {rotation}°", "text": text[:2500]}]
            if not result["lines"]:
                result["warnings"].append("Ảnh chưa nhận diện được chữ; cần xem ảnh gốc")
            else:
                result["complete"] = True  # OCR attempted, not verified.
                result["warnings"].append("Kết quả OCR ảnh CHƯA XÁC MINH; phải so lại nhãn gốc")
        else:
            result["warnings"].append("Ảnh cần bật OCR cục bộ để nhận dạng chữ")
        return result
    if ext == "xls":
        try:
            import xlrd
        except ImportError as exc:
            raise ValueError("Thiếu thư viện xlrd cho Excel .xls") from exc
        book = xlrd.open_workbook(file_contents=data)
        result = {"name": filename, "sha256": hashlib.sha256(data).hexdigest(),
                  "type": ext, "lines": [], "warnings": [], "pages": 0,
                  "complete": True, "verified": False}
        count = 0
        for sheet in book.sheets():
            for ri in range(sheet.nrows):
                if count >= MAX_ROWS:
                    result["complete"] = False
                    result["warnings"].append("Vượt 10.000 dòng; tài liệu chỉ được đọc một phần")
                    break
                text = " | ".join(str(cell).strip() for cell in sheet.row_values(ri)
                                  if str(cell).strip())
                if text:
                    result["lines"].append({"source": f"Sheet {sheet.name}, dòng {ri+1}",
                                            "text": text[:2500]})
                count += 1
            if count >= MAX_ROWS:
                break
        return result
    result = extract_document(filename, data)
    if ext != "pdf" or not ocr:
        return result
    import pymupdf
    recovered = set()
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        for i, page in enumerate(pdf):
            if i >= 800:
                break
            if (page.get_text("text", sort=True) or "").strip():
                continue
            try:
                textpage = page.get_textpage_ocr(language="vie+eng", dpi=160, full=True)
                text = page.get_text("text", textpage=textpage)
            except (RuntimeError, ValueError, OSError):
                result["warnings"].append(f"Trang {i+1}: OCR cục bộ không khả dụng")
                continue
            if text.strip():
                recovered.add(i+1)
                for line in text.splitlines():
                    if line.strip():
                        result["lines"].append({"source": f"Trang {i+1} (OCR)",
                                                "text": line.strip()[:2500]})
    if recovered:
        result["warnings"] = [w for w in result["warnings"]
                              if not (m := re.search(r"Trang (\d+): không có lớp chữ", w))
                              or int(m.group(1)) not in recovered]
        result["warnings"].append(
            f"OCR {len(recovered)} trang: dữ liệu CHƯA XÁC MINH, cần so với bản gốc")
        remaining = [w for w in result["warnings"] if "không có lớp chữ" in w]
        result["complete"] = not remaining and result["complete"] or (
            not remaining and result["pages"] <= 800
            and not any("chỉ xem trước" in w for w in result["warnings"]))
    return result


def identify_codes(document: dict) -> list[dict]:
    return candidate_lots(document)
