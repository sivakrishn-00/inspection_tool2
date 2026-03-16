
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0011_district_latitude_district_longitude"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="emp_id",
            field=models.CharField(
                blank=True,
                help_text="Employee ID (max 20k people)",
                max_length=50,
                null=True,
            ),
        ),
    ]
