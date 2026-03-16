
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0005_inspection_vehicle"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="assigned_service_codes",
            field=models.ManyToManyField(
                blank=True,
                related_name="assigned_users",
                to="authentication.servicecode",
            ),
        ),
    ]
