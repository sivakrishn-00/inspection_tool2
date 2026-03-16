
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0020_alter_userservicecodehistory_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="servicecodehistory",
            options={"ordering": ["-timestamp"]},
        ),
        migrations.RenameField(
            model_name="servicecodehistory",
            old_name="assigned_at",
            new_name="timestamp",
        ),
        migrations.RemoveField(
            model_name="servicecodehistory",
            name="unassigned_at",
        ),
        migrations.AddField(
            model_name="servicecodehistory",
            name="action",
            field=models.CharField(
                choices=[("assigned", "Assigned"), ("unassigned", "Unassigned")],
                default="assigned",
                max_length=20,
            ),
        ),
    ]
