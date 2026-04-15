from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0010_product_is_quick_sale"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryMovement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("RETIRADA", "Retirada"),
                            ("TRANSFER_EXISTENTE", "Transferência para produto existente"),
                            ("TRANSFER_NOVO", "Transferência para novo produto"),
                        ],
                        max_length=30,
                    ),
                ),
                ("source_product_name_snapshot", models.CharField(max_length=120)),
                ("destination_product_name_snapshot", models.CharField(blank=True, max_length=120)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=10)),
                ("reason", models.TextField()),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_movements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "destination_product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movements_in",
                        to="inventory.product",
                    ),
                ),
                (
                    "source_product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movements_out",
                        to="inventory.product",
                    ),
                ),
            ],
        ),
    ]
