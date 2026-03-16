
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0017_userprofile_supervisor_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="inspection_deadline_days",
            field=models.IntegerField(
                default=1,
                help_text="Days allowed before inspection is considered missed.",
            ),
        ),
    ]
