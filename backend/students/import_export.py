import csv
import io
from io import StringIO

from openpyxl import load_workbook
from django.contrib.auth import get_user_model

from students.models import Department, Student

User = get_user_model()

REQUIRED_COLUMNS = [
    "full_name",
    "phone_number",
    "department",
    "year",
    "gender",
    "room_number",
    "password",
]


def normalize_text(value):
    return str(value).strip() if value is not None else ""


def normalize_year(value):
    return normalize_text(value).lower().replace(" ", "_")


def normalize_gender(value):
    return normalize_text(value).lower()


def derive_hostel_from_gender(gender):
    if gender == "male":
        return "boys_hostel"
    if gender == "female":
        return "girls_hostel"
    return None


def get_or_create_department_by_name(name):
    normalized = normalize_text(name)
    if not normalized:
        department, _ = Department.objects.get_or_create(name="Unassigned Department")
        return department
    department, _ = Department.objects.get_or_create(name=normalized)
    return department


def parse_csv_file(uploaded_file):
    uploaded_file.seek(0)
    raw_content = uploaded_file.read()

    decode_errors = []
    content = None
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            content = raw_content.decode(encoding)
            break
        except UnicodeDecodeError as exc:
            decode_errors.append(str(exc))

    if content is None:
        raise ValueError("Could not decode CSV file. Please upload a UTF-8 encoded CSV file.")

    stream = io.StringIO(content)
    reader = csv.DictReader(stream)

    rows = []
    for row in reader:
        cleaned_row = {}
        for key, value in row.items():
            normalized_key = normalize_text(key).lstrip("﻿")
            cleaned_row[normalized_key] = value
        rows.append(cleaned_row)

    return rows


def parse_xlsx_file(uploaded_file):
    uploaded_file.seek(0)
    workbook = load_workbook(uploaded_file)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))

    if not rows:
        return []

    headers = [normalize_text(h) for h in rows[0]]
    data_rows = []

    for row in rows[1:]:
        row_dict = {}
        for index, header in enumerate(headers):
            row_dict[header] = row[index] if index < len(row) else ""
        data_rows.append(row_dict)

    return data_rows


def validate_columns(rows):
    if not rows:
        return False, "The uploaded file is empty."

    first_row = rows[0]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in first_row]

    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    return True, ""


def validate_import_row(row):
    full_name = normalize_text(row.get("full_name"))
    phone_number = normalize_text(row.get("phone_number"))
    department_name = normalize_text(row.get("department"))
    year = normalize_year(row.get("year"))
    gender = normalize_gender(row.get("gender"))
    room_number = normalize_text(row.get("room_number"))
    password = normalize_text(row.get("password"))

    if not full_name:
        raise ValueError("Full name is required.")

    if not phone_number:
        raise ValueError("Phone number is required.")

    if year not in dict(Student.YEAR_CHOICES):
        raise ValueError("Invalid year value. Use year_1, year_2, or year_3.")

    if gender not in dict(Student.GENDER_CHOICES):
        raise ValueError("Invalid gender value. Use male or female.")

    if not room_number:
        raise ValueError("Room number is required.")

    if not room_number.isdigit():
        raise ValueError("Room number must contain numbers only.")

    department = get_or_create_department_by_name(department_name)

    return {
        "full_name": full_name,
        "phone_number": phone_number,
        "department": department,
        "year": year,
        "gender": gender,
        "room_number": room_number,
        "password": password,
        "derived_hostel": derive_hostel_from_gender(gender),
    }


def generate_demo_student_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["full_name", "phone_number", "department", "year", "gender", "room_number", "password"])
    writer.writerow(["Aniket Bondre", "9209803186", "IT", "year_1", "male", "101", "aniket123"])
    writer.writerow(["Aman Verma", "9000000002", "Mechanical Engineering", "year_2", "male", "102", "aman123"])
    writer.writerow(["Sneha Patil", "9000000003", "Computer Technology", "year_1", "female", "201", "sneha123"])
    writer.writerow(["Pooja Kulkarni", "9000000004", "Electronics Engineering", "year_3", "female", "202", "pooja123"])
    writer.writerow(["Rohit Deshmukh", "9000000005", "Civil Engineering", "year_2", "male", "103", "rohit123"])
    return output.getvalue()