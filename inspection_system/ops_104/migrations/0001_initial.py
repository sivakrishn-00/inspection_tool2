
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentication", "0005_inspection_vehicle"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InspectionCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(unique=True)),
                ("order", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name_plural": "Inspection Categories",
            },
        ),
        migrations.CreateModel(
            name="InspectionQuestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.CharField(max_length=255)),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("boolean", "Good / Not Good"),
                            ("condition", "Good / Average / Poor / Not Operational"),
                            (
                                "maintenance",
                                "Maintained / Partially / Not Maintained / Not Available",
                            ),
                            (
                                "equipment",
                                "Equipment (Available/Working/Not Working/Not Available)",
                            ),
                        ],
                        max_length=50,
                    ),
                ),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="ops_104.inspectioncategory",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OpsInspection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "overall_status",
                    models.CharField(default="submitted", max_length=20),
                ),
                (
                    "inspector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ops_inspections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ops_inspections",
                        to="authentication.vehicle",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InspectionAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("response", models.CharField(max_length=50)),
                ("remarks", models.TextField(blank=True, null=True)),
                (
                    "photo",
                    models.ImageField(
                        blank=True, null=True, upload_to="inspection_evidence/%Y/%m/%d/"
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ops_104.inspectionquestion",
                    ),
                ),
                (
                    "inspection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="ops_104.opsinspection",
                    ),
                ),
            ],
        ),
    ]
