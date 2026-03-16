
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0018_role_inspection_deadline_days"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserServiceCodeHistory",
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
                    "assigned_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="user_assignments_made",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "service_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_assignment_history",
                        to="authentication.servicecode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_code_history",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "User Service Code Histories",
                "ordering": ["-assigned_at"],
            },
        ),
    ]
