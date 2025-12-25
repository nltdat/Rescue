# Generated manually to add unique constraint after data cleaning

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_duplicate_phones'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
