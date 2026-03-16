
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0019_userservicecodehistory"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="userservicecodehistory",
            options={
                "ordering": ["-timestamp"],
                "verbose_name_plural": "User Service Code Histories",
            },
        ),
        migrations.RenameField(
            model_name="userservicecodehistory",
            old_name="assigned_at",
            new_name="timestamp",
        ),
        migrations.RemoveField(
            model_name="userservicecodehistory",
            name="assigned_by",
        ),
        migrations.RemoveField(
            model_name="userservicecodehistory",
            name="unassigned_at",
        ),
        migrations.AddField(
            model_name="userservicecodehistory",
            name="action",
            field=models.CharField(
                choices=[("assigned", "Assigned"), ("unassigned", "Unassigned")],
                default="assigned",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userservicecodehistory",
            name="performed_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="actions_performed",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
