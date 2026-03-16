
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0010_mandal_vehicle_mandal"),
    ]

    operations = [
        migrations.AddField(
            model_name="district",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="district",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
