from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, UpdateView

from .forms import CategoryForm, InventoryMovementForm, ProductForm
from .models import Category, InventoryMovement, Product


def _build_form_feedback(form):
    field_labels = {
        "name": "Nome",
        "category_ref": "Categoria",
        "current_stock": "Estoque",
        "min_stock": "Estoque mínimo",
        "sale_price": "Preço de venda",
        "is_quick_sale": "Produto rápido",
        "is_active": "Ativo",
        "movement_type": "Tipo de movimentação",
        "source_product": "Produto de origem",
        "quantity": "Quantidade",
        "reason": "Motivo",
        "destination_product": "Produto de destino",
        "new_product_name": "Nome do novo produto",
        "new_product_category": "Categoria do novo produto",
        "new_product_sale_price": "Preço do novo produto",
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
    movement_form = InventoryMovementForm()
    open_movement_modal = False

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

        if form_type == "movement":
            movement_form = InventoryMovementForm(request.POST)
            product_form = ProductForm()
            category_form = CategoryForm()
            open_movement_modal = True

            if movement_form.is_valid():
                cleaned = movement_form.cleaned_data
                movement_type = cleaned["movement_type"]
                quantity = cleaned["quantity"]
                source_product_id = cleaned["source_product"].pk
                destination_product = cleaned.get("destination_product")

                try:
                    with transaction.atomic():
                        source_product = Product.objects.select_for_update().get(pk=source_product_id)

                        if quantity > source_product.current_stock:
                            raise ValidationError(
                                {
                                    "quantity": (
                                        f"Quantidade maior que o estoque disponível ({source_product.current_stock})."
                                    )
                                }
                            )

                        destination_instance = None
                        if movement_type == InventoryMovement.MovementType.TRANSFER_EXISTING:
                            destination_instance = Product.objects.select_for_update().get(pk=destination_product.pk)
                        elif movement_type == InventoryMovement.MovementType.TRANSFER_NEW:
                            new_name = cleaned["new_product_name"].strip()
                            new_category = cleaned.get("new_product_category")
                            new_sale_price = cleaned.get("new_product_sale_price")
                            destination_instance = Product.objects.create(
                                name=new_name,
                                category_ref=new_category,
                                current_stock=quantity,
                                min_stock=0,
                                sale_price=new_sale_price if new_sale_price is not None else source_product.sale_price,
                                is_quick_sale=False,
                                is_active=True,
                            )
                            destination_product = destination_instance

                        source_product.current_stock = (source_product.current_stock - quantity).quantize(
                            Decimal("0.001")
                        )
                        source_product.save(update_fields=["current_stock"])

                        if movement_type == InventoryMovement.MovementType.TRANSFER_EXISTING and destination_instance:
                            destination_instance.current_stock = (
                                destination_instance.current_stock + quantity
                            ).quantize(Decimal("0.001"))
                            destination_instance.save(update_fields=["current_stock"])

                        InventoryMovement.objects.create(
                            created_by=request.user,
                            movement_type=movement_type,
                            source_product=source_product,
                            source_product_name_snapshot=source_product.name,
                            destination_product=None
                            if movement_type == InventoryMovement.MovementType.WITHDRAW
                            else destination_product,
                            destination_product_name_snapshot=""
                            if movement_type == InventoryMovement.MovementType.WITHDRAW
                            else destination_product.name,
                            quantity=quantity,
                            reason=cleaned["reason"].strip(),
                        )

                        if movement_type == InventoryMovement.MovementType.WITHDRAW:
                            messages.success(request, f"Retirada registrada para {source_product.name}.")
                        elif movement_type == InventoryMovement.MovementType.TRANSFER_EXISTING:
                            messages.success(
                                request,
                                f"Movimentação registrada de {source_product.name} para {destination_product.name}.",
                            )
                        else:
                            messages.success(
                                request,
                                f"Novo produto {destination_product.name} criado a partir da movimentação.",
                            )
                        return redirect("inventory-home")
                except ValidationError as exc:
                    messages.error(request, _validation_errors_to_text(exc))
            else:
                feedback = _build_form_feedback(movement_form)
                messages.error(request, " ".join(feedback) if feedback else "Revise os dados da movimentação.")

        elif form_type == "category":
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
            "movement_form": movement_form,
            "open_movement_modal": open_movement_modal,
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


class InventoryMovementHistoryView(LoginRequiredMixin, View):
    template_name = "inventory/movement_history.html"

    def get(self, request):
        movements_qs = InventoryMovement.objects.select_related(
            "created_by",
            "source_product",
            "destination_product",
        )

        search_term = request.GET.get("q", "").strip()
        movement_type = request.GET.get("type", "").strip()
        start_date = request.GET.get("start_date", "").strip()
        end_date = request.GET.get("end_date", "").strip()

        if search_term:
            movements_qs = movements_qs.filter(
                Q(source_product_name_snapshot__icontains=search_term)
                | Q(destination_product_name_snapshot__icontains=search_term)
                | Q(reason__icontains=search_term)
                | Q(created_by__username__icontains=search_term)
            )
        if movement_type:
            movements_qs = movements_qs.filter(movement_type=movement_type)
        if start_date:
            movements_qs = movements_qs.filter(created_at__date__gte=start_date)
        if end_date:
            movements_qs = movements_qs.filter(created_at__date__lte=end_date)

        movements_qs = movements_qs.order_by("-created_at", "-id")
        paginator = Paginator(movements_qs, 8)
        page_obj = paginator.get_page(request.GET.get("page"))

        summary = movements_qs.aggregate(
            total_movements=Count("id"),
            withdraws=Count("id", filter=Q(movement_type=InventoryMovement.MovementType.WITHDRAW)),
            transfers_existing=Count(
                "id",
                filter=Q(movement_type=InventoryMovement.MovementType.TRANSFER_EXISTING),
            ),
            transfers_new=Count("id", filter=Q(movement_type=InventoryMovement.MovementType.TRANSFER_NEW)),
            total_quantity=Sum("quantity"),
        )

        query_params = {}
        if search_term:
            query_params["q"] = search_term
        if movement_type:
            query_params["type"] = movement_type
        if start_date:
            query_params["start_date"] = start_date
        if end_date:
            query_params["end_date"] = end_date

        return render(
            request,
            self.template_name,
            {
                "movements": page_obj,
                "filter_state": {
                    "q": search_term,
                    "type": movement_type,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "querystring": urlencode(query_params),
                "summary": {
                    "total_movements": summary["total_movements"] or 0,
                    "withdraws": summary["withdraws"] or 0,
                    "transfers_existing": summary["transfers_existing"] or 0,
                    "transfers_new": summary["transfers_new"] or 0,
                    "total_quantity": summary["total_quantity"] or Decimal("0.000"),
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
        messages.success(request, "Produto removido com sucesso.")
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
        messages.success(request, "Categoria removida com sucesso.")
        return super().delete(request, *args, **kwargs)
