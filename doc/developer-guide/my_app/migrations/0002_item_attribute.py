from django.db import migrations, models

from freppledb.common.migrate import AttributeMigration


# Attribute migrations need to inherit from this base class
class Migration(AttributeMigration):

    # Module owning the extended model
    extends_app_label = "input"

    # Defines migrations that are prerequisites for this one
    dependencies = [("my_app", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="item",
            name="attribute_1",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="first attribute",
            ),
        )
    ]
