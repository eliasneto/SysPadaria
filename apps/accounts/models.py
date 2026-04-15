from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        CAIXA = "CAIXA", "Caixa"
        ESTOQUE = "ESTOQUE", "Estoque"
        FINANCEIRO = "FINANCEIRO", "Financeiro"
        GERENTE = "GERENTE", "Gerente"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CAIXA)

    def __str__(self):
        return self.get_full_name() or self.username
