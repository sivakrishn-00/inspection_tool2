
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("erc_104", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ERCGridSection",
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
                ("rows", models.IntegerField(default=3)),
                ("cols", models.IntegerField(default=3)),
                (
                    "icon",
                    models.CharField(
                        choices=[
                            ("chair", "Chair"),
                            ("monitor", "Monitor"),
                            ("bulb", "Light Bulb"),
                            ("ac", "AC Unit"),
                            ("fire", "Fire Extinguisher"),
                            ("door", "Door"),
                            ("headset", "Headset"),
                            ("battery", "Battery"),
                            ("water", "Water Tap"),
                            ("wifi", "WiFi / Server"),
                            ("cctv", "CCTV Camera"),
                        ],
                        default="chair",
                        max_length=50,
                    ),
                ),
                ("prefix", models.CharField(default="S", max_length=10)),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name="ercinspection",
            name="visual_layout_snapshot",
            field=models.TextField(
                blank=True, help_text="JSON snapshot of the grid state", null=True
            ),
        ),
    ]
