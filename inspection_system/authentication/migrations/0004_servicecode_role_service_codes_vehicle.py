
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_inspection"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceCode",
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
                (
                    "code",
                    models.CharField(
                        help_text="Service Code (e.g., K, A1)",
                        max_length=20,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name="role",
            name="service_codes",
            field=models.ManyToManyField(
                blank=True, related_name="roles", to="authentication.servicecode"
            ),
        ),
        migrations.CreateModel(
            name="Vehicle",
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
                ("registration_number", models.CharField(max_length=50, unique=True)),
                ("model_name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "service_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vehicles",
                        to="authentication.servicecode",
                    ),
                ),
            ],
        ),
    ]
