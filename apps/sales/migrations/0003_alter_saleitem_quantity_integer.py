from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0002_sale_saleitem"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saleitem",
            name="quantity",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
