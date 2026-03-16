
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0013_role_is_exclusive_service_access"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vehicle",
            name="service_code",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="current_vehicle",
                to="authentication.servicecode",
            ),
        ),
        migrations.CreateModel(
            name="ServiceCodeHistory",
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
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("unassigned_at", models.DateTimeField(blank=True, null=True)),
                (
                    "service_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="history",
                        to="authentication.servicecode",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_history",
                        to="authentication.vehicle",
                    ),
                ),
            ],
        ),
    ]
