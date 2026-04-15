from django.db import models


class FinancialEntry(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.description
