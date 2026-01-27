from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0022_flooroption_requirement_preferred_floors'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='number_of_floors',
            field=models.PositiveSmallIntegerField(choices=[(1, '1 piso'), (2, '2 pisos'), (3, '3 pisos'), (4, '4 pisos'), (5, '5 pisos')], null=True, blank=True, verbose_name='Cantidad de pisos'),
        ),
    ]
