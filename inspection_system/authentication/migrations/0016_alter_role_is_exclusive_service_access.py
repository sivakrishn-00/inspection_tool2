
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0015_role_is_single_service_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="role",
            name="is_exclusive_service_access",
            field=models.BooleanField(
                default=True,
                help_text="If true, users with this role see only unassigned codes.",
            ),
        ),
    ]
