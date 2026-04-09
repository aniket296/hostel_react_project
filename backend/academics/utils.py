from .models import Subject


def get_or_create_subject_by_name(name):
    normalized = " ".join(name.strip().split())
    subject, _ = Subject.objects.get_or_create(name=normalized)
    return subject


def get_file_icon(file_name):
    file_name = (file_name or "").lower()
    if file_name.endswith(".pdf"):
        return "pdf"
    if file_name.endswith((".doc", ".docx")):
        return "word"
    if file_name.endswith((".ppt", ".pptx")):
        return "ppt"
    if file_name.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    return "file"