from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0003_add_question_bank"),
    ]

    operations = [
        migrations.AddField(
            model_name="academicfile",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]