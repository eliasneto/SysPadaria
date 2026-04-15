from django import forms
from django.db.models import Q
from decimal import Decimal

from .models import Category, InventoryMovement, Product


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


class InventoryMovementForm(forms.Form):
    movement_type = forms.ChoiceField(
        choices=InventoryMovement.MovementType.choices,
        widget=forms.Select(attrs={"class": "form-select sys-input"}),
    )
    source_product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by("name"),
        widget=forms.Select(attrs={"class": "form-select sys-input"}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={"class": "form-control sys-input", "step": "1", "inputmode": "numeric"}
        ),
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control sys-input", "rows": 3}),
    )
    destination_product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Selecione um produto",
        widget=forms.Select(attrs={"class": "form-select sys-input"}),
    )
    new_product_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control sys-input"}),
    )
    new_product_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Sem categoria",
        widget=forms.Select(attrs={"class": "form-select sys-input"}),
    )
    new_product_sale_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        widget=forms.NumberInput(
            attrs={"class": "form-control sys-input", "step": "0.01", "inputmode": "decimal"}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get("movement_type")
        source_product = cleaned_data.get("source_product")
        quantity = cleaned_data.get("quantity")
        destination_product = cleaned_data.get("destination_product")
        new_product_name = (cleaned_data.get("new_product_name") or "").strip()

        if source_product and quantity is not None and quantity > source_product.current_stock:
            self.add_error(
                "quantity",
                f"Quantidade maior que o estoque disponível ({source_product.current_stock}).",
            )

        if movement_type == InventoryMovement.MovementType.TRANSFER_EXISTING:
            if not destination_product:
                self.add_error("destination_product", "Selecione o produto de destino.")
            elif source_product and destination_product.pk == source_product.pk:
                self.add_error("destination_product", "O produto de destino não pode ser o mesmo de origem.")

        if movement_type == InventoryMovement.MovementType.TRANSFER_NEW and not new_product_name:
            self.add_error("new_product_name", "Informe o nome do novo produto.")

        return cleaned_data
