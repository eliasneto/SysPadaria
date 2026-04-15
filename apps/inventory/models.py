from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=120)
    category_ref = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_quick_sale = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.min_stock > self.current_stock:
            raise ValidationError(
                {"min_stock": "O estoque mínimo não pode ser maior que o estoque atual."}
            )

        if self.is_quick_sale:
            quick_qs = Product.objects.filter(is_quick_sale=True, is_active=True)
            if self.pk:
                quick_qs = quick_qs.exclude(pk=self.pk)
            if quick_qs.count() >= 12:
                raise ValidationError(
                    {"is_quick_sale": "Selecione no máximo 12 produtos para os produtos rápidos."}
                )
