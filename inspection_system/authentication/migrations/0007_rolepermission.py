
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0006_userprofile_assigned_service_codes"),
    ]

    operations = [
        migrations.CreateModel(
            name="RolePermission",
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
                ("feature_code", models.CharField(max_length=100)),
                (
                    "description",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("is_enabled", models.BooleanField(default=False)),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permissions",
                        to="authentication.role",
                    ),
                ),
            ],
            options={
                "unique_together": {("role", "feature_code")},
            },
        ),
    ]
