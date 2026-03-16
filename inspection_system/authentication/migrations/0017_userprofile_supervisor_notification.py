
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0016_alter_role_is_exclusive_service_access"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                help_text="The person this user reports to.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subordinates",
                to="authentication.userprofile",
            ),
        ),
        migrations.CreateModel(
            name="Notification",
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
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("alert", "Alert"),
                            ("warning", "Warning"),
                            ("info", "Info"),
                            ("success", "Success"),
                        ],
                        default="info",
                        max_length=20,
                    ),
                ),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "link",
                    models.CharField(
                        blank=True,
                        help_text="Optional link to action",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
