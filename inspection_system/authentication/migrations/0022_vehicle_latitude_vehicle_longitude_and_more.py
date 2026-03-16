
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0021_alter_servicecodehistory_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="VehicleLocationHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "service_code",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="authentication.servicecode",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_history",
                        to="authentication.vehicle",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
    ]
