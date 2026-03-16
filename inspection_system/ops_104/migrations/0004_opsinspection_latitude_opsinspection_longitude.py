
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ops_104", "0003_alter_opsinspection_district_delete_district"),
    ]

    operations = [
        migrations.AddField(
            model_name="opsinspection",
            name="latitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AddField(
            model_name="opsinspection",
            name="longitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
    ]
