
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0004_servicecode_role_service_codes_vehicle"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspection",
            name="vehicle",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="inspections",
                to="authentication.vehicle",
            ),
        ),
    ]
