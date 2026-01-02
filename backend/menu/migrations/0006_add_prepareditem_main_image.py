from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0005_merge_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='prepareditem',
            name='main_image',
            field=models.ImageField(blank=True, null=True, upload_to='prepared_items/'),
        ),
    ]
