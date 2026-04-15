from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView

from .forms import CategoryForm, ProductForm
from .models import Category, Product


def _build_form_feedback(form):
    field_labels = {
        "name": "Nome",
        "category_ref": "Categoria",
        "current_stock": "Estoque",
        "min_stock": "Estoque mínimo",
        "sale_price": "Preço de venda",
        "is_quick_sale": "Produto rápido",
        "is_active": "Ativo",
    }
    errors = []
    errors.extend([str(err) for err in form.non_field_errors()])
    for field, field_errors in form.errors.items():
        if field == "__all__":
            continue
        label = field_labels.get(field, field)
        for err in field_errors:
            errors.append(f"{label}: {err}")
    return errors


def _validation_errors_to_text(error):
    if hasattr(error, "message_dict"):
        messages_list = []
        for field, field_errors in error.message_dict.items():
            for err in field_errors:
                messages_list.append(f"{field}: {err}")
        return " ".join(messages_list)
    if hasattr(error, "messages"):
        return " ".join(error.messages)
    return str(error)


def inventory_home(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "quick_toggle":
            product_id = request.POST.get("product_id")
            desired_state = request.POST.get("is_quick_sale") == "on"
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                messages.error(request, "Produto não encontrado.")
                return redirect("inventory-home")

            product.is_quick_sale = desired_state
            try:
                product.full_clean()
                product.save()
                if desired_state:
                    messages.success(request, f"{product.name} adicionado aos produtos rápidos.")
                else:
                    messages.success(request, f"{product.name} removido dos produtos rápidos.")
                return redirect("inventory-home")
            except ValidationError as exc:
                messages.error(request, _validation_errors_to_text(exc))
                return redirect("inventory-home")
        if form_type == "category":
            category_form = CategoryForm(request.POST)
            product_form = ProductForm()
            if category_form.is_valid():
                category_form.save()
                messages.success(request, "Categoria cadastrada com sucesso.")
                return redirect("inventory-home")
            feedback = _build_form_feedback(category_form)
            messages.error(request, " ".join(feedback) if feedback else "Revise os dados da categoria.")
        else:
            product_form = ProductForm(request.POST)
            category_form = CategoryForm()
            if product_form.is_valid():
                product_form.save()
                messages.success(request, "Produto cadastrado com sucesso.")
                return redirect("inventory-home")
            feedback = _build_form_feedback(product_form)
            messages.error(request, " ".join(feedback) if feedback else "Revise os dados do produto.")
    else:
        product_form = ProductForm()
        category_form = CategoryForm()

    products_qs = Product.objects.select_related("category_ref").order_by("name")
    search_term = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()
    quick_sale_filter = request.GET.get("quick_sale", "").strip()

    if search_term:
        products_qs = products_qs.filter(name__icontains=search_term)
    if category_filter:
        products_qs = products_qs.filter(category_ref_id=category_filter)
    if quick_sale_filter == "1":
        products_qs = products_qs.filter(is_quick_sale=True)

    paginator = Paginator(products_qs, 8)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = {}
    if search_term:
        query_params["q"] = search_term
    if category_filter:
        query_params["category"] = category_filter
    if quick_sale_filter == "1":
        query_params["quick_sale"] = "1"

    summary = Product.objects.aggregate(
        total_products=Count("id"),
        active_products=Count("id", filter=Q(is_active=True)),
        quick_products=Count("id", filter=Q(is_active=True, is_quick_sale=True)),
        stock_total=Sum("current_stock"),
    )
    low_stock_count = Product.objects.filter(current_stock__lte=models.F("min_stock")).count()

    return render(
        request,
        "inventory/home.html",
        {
            "form": product_form,
            "category_form": category_form,
            "products": page_obj,
            "categories": Category.objects.order_by("name"),
            "filter_state": {
                "q": search_term,
                "category": category_filter,
                "quick_sale": quick_sale_filter == "1",
            },
            "querystring": urlencode(query_params),
            "summary": {
                "total_products": summary["total_products"] or 0,
                "active_products": summary["active_products"] or 0,
                "quick_products": summary["quick_products"] or 0,
                "stock_total": summary["stock_total"] or Decimal("0"),
                "low_stock_count": low_stock_count,
            },
        },
    )


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory-home")

    def form_valid(self, form):
        messages.success(self.request, "Produto atualizado com sucesso.")
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "inventory/product_confirm_delete.html"
    success_url = reverse_lazy("inventory-home")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Produto removido com sucesso.")
        return super().delete(request, *args, **kwargs)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory-home")

    def form_valid(self, form):
        messages.success(self.request, "Categoria atualizada com sucesso.")
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "inventory/category_confirm_delete.html"
    success_url = reverse_lazy("inventory-home")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Categoria removida com sucesso.")
        return super().delete(request, *args, **kwargs)
