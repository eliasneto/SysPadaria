from django import forms
from django.db.models import Q

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control sys-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProductForm(forms.ModelForm):
    category_ref = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Sem categoria",
        widget=forms.Select(attrs={"class": "form-select sys-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Category.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.category_ref_id:
            queryset = Category.objects.filter(Q(is_active=True) | Q(pk=self.instance.category_ref_id))
        self.fields["category_ref"].queryset = queryset.order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        current_stock = cleaned_data.get("current_stock")
        min_stock = cleaned_data.get("min_stock")

        if current_stock is not None and min_stock is not None and min_stock > current_stock:
            self.add_error("min_stock", "O estoque mínimo não pode ser maior que o estoque atual.")

        return cleaned_data

    class Meta:
        model = Product
        fields = [
            "name",
            "category_ref",
            "current_stock",
            "min_stock",
            "sale_price",
            "is_quick_sale",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control sys-input"}),
            "current_stock": forms.NumberInput(
                attrs={"class": "form-control sys-input", "step": "0.001", "inputmode": "decimal"}
            ),
            "min_stock": forms.NumberInput(
                attrs={"class": "form-control sys-input", "step": "0.001", "inputmode": "decimal"}
            ),
            "sale_price": forms.NumberInput(
                attrs={"class": "form-control sys-input", "step": "0.01", "inputmode": "decimal"}
            ),
            "is_quick_sale": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
