
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0014_alter_vehicle_service_code_servicecodehistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="is_single_service_code",
            field=models.BooleanField(
                default=False,
                help_text="If true, users can select only one code (Radio buttons). details",
            ),
        ),
    ]
