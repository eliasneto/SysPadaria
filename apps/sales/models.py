from django.conf import settings
from django.db import models

from apps.inventory.models import Product


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "DINHEIRO", "Dinheiro"
        PIX = "PIX", "PIX"
        DEBIT = "DEBITO", "Cartão de débito"
        CREDIT = "CREDITO", "Cartão de crédito"
        STORE = "FIADO", "Fiado"

    class Status(models.TextChoices):
        OPEN = "ABERTA", "Aberta"
        FINISHED = "FINALIZADA", "Finalizada"
        CANCELED = "CANCELADA", "Cancelada"

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
    )
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.FINISHED)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Venda #{self.pk or 'nova'}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product} x {self.quantity}"
