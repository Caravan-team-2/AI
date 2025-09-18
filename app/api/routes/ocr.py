from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict, Any
from PIL import Image
import pytesseract
import io
import re


router = APIRouter()


def _extract_fields(text: str) -> Dict[str, Any]:
	lines = [line.strip() for line in text.splitlines() if line.strip()]
	joined = "\n".join(lines)

	# Birthdate patterns: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
	birthdate_match = re.search(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4}|\d{4}[\/-]\d{2}[\/-]\d{2})\b", joined)
	birthdate = birthdate_match.group(1) if birthdate_match else None

	# ID number patterns with common labels (CIN, ID, N°)
	id_patterns = [
		r"(?:CIN|ID|Identifiant|Numero|Numéro|N°)\s*[:#-]?\s*([A-Z0-9]{5,})",
		r"\b([A-Z]{1,3}\d{5,})\b",
		r"\b(\d{8,})\b",
	]
	id_number = None
	for pattern in id_patterns:
		m = re.search(pattern, joined, flags=re.IGNORECASE)
		if m:
			id_number = m.group(1)
			break

	# Name extraction: try lines starting with labels, else longest uppercase line
	name = None
	label_patterns = [
		r"^(?:Name|Nom)\s*[:\-]\s*(.+)$",
		r"^(?:Prénom|Prenom|First\s*Name)\s*[:\-]\s*(.+)$",
	]
	for line in lines:
		for pat in label_patterns:
			m = re.search(pat, line, flags=re.IGNORECASE)
			if m:
				name = m.group(1).strip()
				break
		if name:
			break

	if not name:
		upper_lines = [ln for ln in lines if ln.isupper() and 3 <= len(ln) <= 60]
		if upper_lines:
			name = max(upper_lines, key=len)

	return {"id_number": id_number, "birthdate": birthdate, "name": name}


@router.post("/extract", summary="Extract data from ID card image")
async def extract_id_data(file: UploadFile = File(...)) -> Dict[str, Any]:
	if not file.content_type or not file.content_type.startswith("image/"):
		raise HTTPException(status_code=400, detail="File must be an image")

	content = await file.read()
	try:
		image = Image.open(io.BytesIO(content))
		image = image.convert("RGB")
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid image file")

	# Run OCR
	try:
		text = pytesseract.image_to_string(image, lang="eng")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

	fields = _extract_fields(text)
	return {"raw_text": text, "fields": fields}


