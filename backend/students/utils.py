from .models import Department


def get_unassigned_department():
    department, _ = Department.objects.get_or_create(name="Unassigned Department")
    return department