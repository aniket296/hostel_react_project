from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from students.models import Department, Student

User = get_user_model()


class Command(BaseCommand):
    help = "Generate demo student data"

    def handle(self, *args, **options):
        departments = [
            "Information Technology",
            "Computer Technology",
            "Civil Engineering",
        ]

        department_objects = []
        for dept_name in departments:
            dept, _ = Department.objects.get_or_create(name=dept_name)
            department_objects.append(dept)

        demo_students = [
            {
                "full_name": "Aarav Patil",
                "phone_number": "9000000001",
                "department": department_objects[0],
                "year": "year_1",
                "gender": "male",
                "room_number": "101",
                "password": "demo123",
            },
            {
                "full_name": "Riya Sharma",
                "phone_number": "9000000002",
                "department": department_objects[1],
                "year": "year_2",
                "gender": "female",
                "room_number": "201",
                "password": "demo123",
            },
            {
                "full_name": "Kunal Verma",
                "phone_number": "9000000003",
                "department": department_objects[2],
                "year": "year_3",
                "gender": "male",
                "room_number": "102",
                "password": "demo123",
            },
            {
                "full_name": "Sneha Joshi",
                "phone_number": "9000000004",
                "department": department_objects[0],
                "year": "year_1",
                "gender": "female",
                "room_number": "202",
                "password": "demo123",
            },
            {
                "full_name": "Manav Kulkarni",
                "phone_number": "9000000005",
                "department": department_objects[1],
                "year": "year_2",
                "gender": "male",
                "room_number": "103",
                "password": "demo123",
            },
        ]

        created = 0
        updated = 0

        for item in demo_students:
            existing_user = User.objects.filter(phone_number=item["phone_number"]).first()

            if existing_user and hasattr(existing_user, "student_profile"):
                student = existing_user.student_profile
                student.full_name = item["full_name"]
                student.phone_number = item["phone_number"]
                student.department = item["department"]
                student.year = item["year"]
                student.gender = item["gender"]
                student.room_number = item["room_number"]
                student.save()

                existing_user.username = item["phone_number"]
                existing_user.phone_number = item["phone_number"]
                existing_user.set_password(item["password"])
                existing_user.save()
                updated += 1
            else:
                user = User.objects.create_user(
                    username=item["phone_number"],
                    phone_number=item["phone_number"],
                    password=item["password"],
                    role="student",
                    is_active=True,
                )
                Student.objects.create(
                    user=user,
                    full_name=item["full_name"],
                    phone_number=item["phone_number"],
                    department=item["department"],
                    year=item["year"],
                    gender=item["gender"],
                    room_number=item["room_number"],
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demo data generation complete. Created: {created}, Updated: {updated}"
        ))