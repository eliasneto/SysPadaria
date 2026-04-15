from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0008_backfill_categories"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="category",
        ),
    ]
