from django.db import migrations, models


def create_zoning_options(apps, schema_editor):
    ZoningOption = apps.get_model('properties', 'ZoningOption')
    names = [
        ('URBANO', 'urbano', 1),
        ('RURAL', 'rural', 2),
        ('INDUSTRIAL', 'industrial', 3),
        ('COMERCIAL', 'comercial', 4),
    ]
    for idx, (name, code, order) in enumerate(names, start=1):
        ZoningOption.objects.create(name=name.capitalize(), code=code, order=order, is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0024_requirement_ascensor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZoningOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(blank=True, max_length=20, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'zoning_options',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='requirement',
            name='zonificaciones',
            field=models.ManyToManyField(blank=True, related_name='requirements', to='properties.ZoningOption'),
        ),
        migrations.RunPython(create_zoning_options),
    ]
