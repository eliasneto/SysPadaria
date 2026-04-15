from decimal import Decimal

from django.db import migrations


def create_demo_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")

    demo_products = [
        ("Pão francês", Decimal("120.000"), Decimal("1.50")),
        ("Pão de queijo", Decimal("80.000"), Decimal("3.50")),
        ("Café coado", Decimal("50.000"), Decimal("4.00")),
        ("Bolo caseiro", Decimal("15.000"), Decimal("12.00")),
        ("Sonho", Decimal("25.000"), Decimal("7.00")),
        ("Suco natural", Decimal("30.000"), Decimal("6.50")),
    ]

    for name, stock, price in demo_products:
        Product.objects.get_or_create(
            name=name,
            defaults={"current_stock": stock, "sale_price": price},
        )


def remove_demo_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(
        name__in=[
            "Pão francês",
            "Pão de queijo",
            "Café coado",
            "Bolo caseiro",
            "Sonho",
            "Suco natural",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_product_sale_price"),
    ]

    operations = [
        migrations.RunPython(create_demo_products, remove_demo_products),
    ]
