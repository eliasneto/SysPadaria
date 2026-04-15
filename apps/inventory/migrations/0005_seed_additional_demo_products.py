from decimal import Decimal

from django.db import migrations


def seed_additional_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")

    demo_products = [
        ("Torta de frango", Decimal("18.000"), Decimal("9.50")),
        ("Pão integral", Decimal("40.000"), Decimal("2.50")),
        ("Misto quente", Decimal("35.000"), Decimal("6.00")),
    ]

    for name, stock, price in demo_products:
        Product.objects.get_or_create(
            name=name,
            defaults={"current_stock": stock, "sale_price": price},
        )


def unseed_additional_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(
        name__in=["Torta de frango", "Pão integral", "Misto quente"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_seed_missing_demo_products"),
    ]

    operations = [
        migrations.RunPython(seed_additional_products, unseed_additional_products),
    ]
