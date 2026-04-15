from django.db import migrations, models


def seed_quick_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    quick_products = Product.objects.filter(is_active=True).order_by("name")[:12]
    Product.objects.filter(pk__in=[product.pk for product in quick_products]).update(is_quick_sale=True)


def unseed_quick_products(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.update(is_quick_sale=False)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0009_remove_legacy_category_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_quick_sale",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_quick_products, unseed_quick_products),
    ]
