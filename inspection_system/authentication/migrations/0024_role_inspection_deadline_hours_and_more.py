
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0023_alter_vehicle_latitude_alter_vehicle_longitude"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="inspection_deadline_hours",
            field=models.IntegerField(default=0, help_text="Additional hours allowed."),
        ),
        migrations.AddField(
            model_name="role",
            name="inspection_deadline_minutes",
            field=models.IntegerField(
                default=0, help_text="Additional minutes allowed."
            ),
        ),
    ]
