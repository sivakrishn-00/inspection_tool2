
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0009_district_alter_inspection_id_alter_project_id_and_more",
        ),
        ("ops_104", "0002_district_opsinspection_district"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opsinspection",
            name="district",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="authentication.district",
            ),
        ),
        migrations.DeleteModel(
            name="District",
        ),
    ]
