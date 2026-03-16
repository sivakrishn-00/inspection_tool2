
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("erc_104", "0002_ercgridsection_ercinspection_visual_layout_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="ercgridsection",
            name="total_items",
            field=models.IntegerField(
                blank=True,
                help_text="Total items to render. If set, overrides rows*cols.",
                null=True,
            ),
        ),
    ]
