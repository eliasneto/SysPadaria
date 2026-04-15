from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_product_sale_price"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sales", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SaleItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=3, default=1, max_digits=10)),
                ("unit_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.product")),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="sales.sale")),
            ],
        ),
        migrations.AddField(
            model_name="sale",
            name="created_by",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sales", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="sale",
            name="payment_method",
            field=models.CharField(choices=[("DINHEIRO", "Dinheiro"), ("PIX", "PIX"), ("DEBITO", "Cartão de débito"), ("CREDITO", "Cartão de crédito"), ("FIADO", "Fiado")], max_length=20),
        ),
        migrations.AddField(
            model_name="sale",
            name="status",
            field=models.CharField(choices=[("ABERTA", "Aberta"), ("FINALIZADA", "Finalizada"), ("CANCELADA", "Cancelada")], default="FINALIZADA", max_length=20),
        ),
    ]
