
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0022_vehicle_latitude_vehicle_longitude_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vehicle",
            name="latitude",
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="longitude",
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
    ]
