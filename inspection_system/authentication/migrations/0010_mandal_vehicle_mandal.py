
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0009_district_alter_inspection_id_alter_project_id_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Mandal",
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
                ("name", models.CharField(max_length=100)),
                (
                    "district",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mandals",
                        to="authentication.district",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("name", "district")},
            },
        ),
        migrations.AddField(
            model_name="vehicle",
            name="mandal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vehicles",
                to="authentication.mandal",
            ),
        ),
    ]
