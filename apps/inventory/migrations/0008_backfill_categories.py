from django.db import migrations


def create_and_link_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    Product = apps.get_model("inventory", "Product")

    category_map = {
        "Pães": ["Pão francês", "Pão integral", "Pão de queijo", "Misto quente"],
        "Bebidas": ["Café coado", "Suco natural"],
        "Doces": ["Bolo caseiro", "Sonho"],
        "Salgados": ["Torta de frango"],
        "Outros": [],
    }

    categories = {}
    for category_name in category_map:
        categories[category_name] = Category.objects.get_or_create(name=category_name)[0]

    for product in Product.objects.all():
        legacy_name = (product.category or "").strip()
        if legacy_name:
            category = Category.objects.get_or_create(name=legacy_name)[0]
        else:
            category = categories["Outros"]
            for category_name, product_names in category_map.items():
                if product.name in product_names:
                    category = categories[category_name]
                    break
        product.category_ref = category
        product.save(update_fields=["category_ref"])


def unlink_categories(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.update(category_ref=None)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0007_category_and_product_category_ref"),
    ]

    operations = [
        migrations.RunPython(create_and_link_categories, unlink_categories),
    ]
