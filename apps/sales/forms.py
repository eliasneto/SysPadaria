from django import forms
from django.forms import inlineformset_factory

from apps.inventory.models import Product

from .models import Sale, SaleItem


PAYMENT_CHOICES = (
    ("CREDITO", "Cartão de crédito"),
    ("DEBITO", "Cartão de débito"),
    ("PIX", "PIX"),
    ("DINHEIRO", "Dinheiro"),
)


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["payment_method"]
        widgets = {
            "payment_method": forms.RadioSelect(choices=PAYMENT_CHOICES),
        }


class SaleItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")

    class Meta:
        model = SaleItem
        fields = ["product", "quantity"]
        widgets = {
            "product": forms.HiddenInput(),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control sys-input text-center fw-semibold",
                    "min": "1",
                    "step": "1",
                    "inputmode": "numeric",
                }
            ),
        }


SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    fields=["product", "quantity"],
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=False,
)
