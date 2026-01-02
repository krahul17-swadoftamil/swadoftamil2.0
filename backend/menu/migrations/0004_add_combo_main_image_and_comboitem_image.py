from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_populate_combo_code_and_add_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='combo',
            name='main_image',
            field=models.ImageField(blank=True, null=True, upload_to='combos/'),
        ),
        migrations.AddField(
            model_name='comboitem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='combo_item_images/'),
        ),
    ]
