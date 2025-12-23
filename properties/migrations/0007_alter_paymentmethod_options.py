from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0006_paymentmethod_alter_propertyfinancialinfo_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="paymentmethod",
            options={"db_table": "payment_methods", "ordering": ("order", "name")},
        ),
    ]
