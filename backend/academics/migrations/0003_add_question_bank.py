from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0002_academicfile_course_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="academicfile",
            name="file_type",
            field=models.CharField(
                choices=[
                    ("pyq_pt", "PYQ PT"),
                    ("pyq_semester", "PYQ Semester"),
                    ("notes", "Notes"),
                    ("question_bank", "Question Bank"),
                    ("curriculum", "Curriculum"),
                ],
                max_length=20,
            ),
        ),
    ]
