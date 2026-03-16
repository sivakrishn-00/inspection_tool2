
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0012_userprofile_emp_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="is_exclusive_service_access",
            field=models.BooleanField(
                default=False,
                help_text="If true, users with this role see only unassigned codes.",
            ),
        ),
    ]
