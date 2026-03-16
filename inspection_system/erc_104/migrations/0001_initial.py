
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ERCCategory",
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
                "verbose_name_plural": "ERC Categories",
            },
        ),
        migrations.CreateModel(
            name="ERCCenter",
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
                ("location", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="ERCInspection",
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
                    "center",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="erc_inspections",
                        to="erc_104.erccenter",
                    ),
                ),
                (
                    "inspector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="erc_inspections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ERCItem",
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
                    "item_type",
                    models.CharField(
                        choices=[
                            ("boolean", "Good / Not Good"),
                            ("condition", "Good / Damaged / Missing"),
                            ("availability", "Available / Not Available"),
                        ],
                        default="boolean",
                        max_length=50,
                    ),
                ),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="erc_104.erccategory",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ERCResponse",
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
                        blank=True, null=True, upload_to="erc_evidence/%Y/%m/%d/"
                    ),
                ),
                (
                    "inspection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="erc_104.ercinspection",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="erc_104.ercitem",
                    ),
                ),
            ],
        ),
    ]
