
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ops_104", "0004_opsinspection_latitude_opsinspection_longitude"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="opsinspection",
            name="latitude",
        ),
        migrations.RemoveField(
            model_name="opsinspection",
            name="longitude",
        ),
    ]
