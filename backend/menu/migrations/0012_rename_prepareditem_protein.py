from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0011_alter_combo_options_alter_comboimage_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="prepareditem",
            old_name="protein",
            new_name="protein_per_unit",
        ),
    ]
