from django.db import migrations, models
import django.utils.timezone


# Migrations inherit from this class
class Migration(migrations.Migration):

    # First migration of this app.
    # Subsequent migrations will instead have a dependencies field that
    # defines the proper sequence of migrations.
    initial = True

    # Defines the migration operations: such as CreateModel, AlterField, DeleteModel,
    # AddIndex, RunSQL, RunPython, etc...
    operations = [
        migrations.CreateModel(
            name="My_Model",
            fields=[
                (
                    "source",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="source",
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                (
                    "charfield",
                    models.CharField(
                        blank=True,
                        help_text="A sample character field",
                        max_length=300,
                        null=True,
                        verbose_name="charfield",
                    ),
                ),
                (
                    "booleanfield",
                    models.BooleanField(
                        blank=True,
                        default=True,
                        help_text="A sample boolean field",
                        verbose_name="booleanfield",
                    ),
                ),
                (
                    "decimalfield",
                    models.DecimalField(
                        decimal_places=8,
                        default="0.00",
                        help_text="A sample decimal field",
                        max_digits=20,
                        verbose_name="decimalfield",
                    ),
                ),
            ],
            options={
                "verbose_name": "my model",
                "verbose_name_plural": "my models",
                "db_table": "my_model",
                "ordering": ["name"],
                "abstract": False,
            },
        )
    ]
