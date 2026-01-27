from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0023_requirement_number_of_floors'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='ascensor',
            field=models.CharField(choices=[('yes', 'Sí'), ('no', 'No')], max_length=3, null=True, blank=True, verbose_name='Ascensor'),
        ),
    ]
