from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.inventory.models import Product

from .forms import PAYMENT_CHOICES, SaleForm, SaleItemFormSet
from .models import Sale


class SalesHomeView(LoginRequiredMixin, View):
    template_name = "sales/sale_form.html"
    formset_prefix = SaleItemFormSet().prefix

    def _build_feedback(self, form, formset):
        field_labels = {
            "payment_method": "Forma de pagamento",
            "product": "Produto",
            "quantity": "Quantidade",
        }
        errors = []
        errors.extend([str(err) for err in form.non_field_errors()])
        for field, field_errors in form.errors.items():
            if field == "__all__":
                continue
            for err in field_errors:
                label = field_labels.get(field, field)
                errors.append(f"{label}: {err}")
        for index, row_errors in enumerate(formset.errors, start=1):
            for field, field_errors in row_errors.items():
                for err in field_errors:
                    label = field_labels.get(field, field)
                    errors.append(f"Item {index} - {label}: {err}")
        errors.extend([str(err) for err in formset.non_form_errors()])
        return errors

    def _selected_items_from_post(self, request, products):
        selected_items = []
        selected_product_ids = []
        product_map = {str(product.id): product for product in products}
        total_forms = int(request.POST.get(f"{self.formset_prefix}-TOTAL_FORMS", "0") or "0")

        for index in range(total_forms):
            product_id = request.POST.get(f"{self.formset_prefix}-{index}-product")
            quantity = request.POST.get(f"{self.formset_prefix}-{index}-quantity", "1") or "1"
            product = product_map.get(str(product_id))
            if not product:
                continue

            selected_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": product.sale_price,
                }
            )
            selected_product_ids.append(product.id)

        return selected_items, selected_product_ids

    def _collect_sale_items(self, formset):
        sale_items = []
        for item_form in formset:
            if not item_form.cleaned_data:
                continue
            sale_items.append(
                {
                    "product": item_form.cleaned_data["product"],
                    "quantity": int(item_form.cleaned_data["quantity"]),
                }
            )
        return sale_items

    def _render(self, request, form, formset, products, selected_items, selected_product_ids):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "quick_products": products,
                "selected_items": selected_items,
                "selected_product_ids": selected_product_ids,
                "payment_choices": PAYMENT_CHOICES,
                "sale_count": Sale.objects.count(),
            },
        )

    def get(self, request):
        form = SaleForm()
        formset = SaleItemFormSet(instance=Sale())
        products = list(Product.objects.filter(is_active=True, is_quick_sale=True).order_by("name")[:12])
        return self._render(request, form, formset, products, [], [])

    def post(self, request):
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST, instance=Sale())
        products = list(Product.objects.filter(is_active=True, is_quick_sale=True).order_by("name")[:12])
        selected_items, selected_product_ids = self._selected_items_from_post(request, products)

        if form.is_valid() and formset.is_valid():
            sale_items = self._collect_sale_items(formset)
            if not sale_items:
                messages.error(request, "Adicione pelo menos um item à venda.")
                return self._render(request, form, formset, products, selected_items, selected_product_ids)

            try:
                with transaction.atomic():
                    requested_quantities = defaultdict(int)
                    for item in sale_items:
                        requested_quantities[item["product"].pk] += item["quantity"]

                    locked_products = {
                        product.pk: product
                        for product in Product.objects.select_for_update().filter(
                            pk__in=requested_quantities.keys()
                        )
                    }

                    for product_id, requested_quantity in requested_quantities.items():
                        product = locked_products.get(product_id)
                        if product is None:
                            raise ValidationError("Um dos produtos selecionados não foi encontrado.")

                        if product.current_stock < Decimal(requested_quantity):
                            raise ValidationError(
                                f"Estoque insuficiente para {product.name}. "
                                f"Disponível: {product.current_stock}, solicitado: {requested_quantity}."
                            )

                    sale = form.save(commit=False)
                    sale.created_by = request.user
                    sale.status = Sale.Status.FINISHED
                    sale.total = Decimal("0.00")
                    sale.save()

                    total = Decimal("0.00")
                    updated_stock = {
                        pk: product.current_stock
                        for pk, product in locked_products.items()
                    }

                    for item in sale_items:
                        product = locked_products[item["product"].pk]
                        quantity = item["quantity"]
                        unit_price = product.sale_price or Decimal("0.00")
                        subtotal = (unit_price * Decimal(quantity)).quantize(Decimal("0.01"))
                        sale.items.create(
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price,
                            subtotal=subtotal,
                        )
                        updated_stock[product.pk] = (updated_stock[product.pk] - Decimal(quantity)).quantize(
                            Decimal("0.001")
                        )
                        total += subtotal

                    for product_id, stock_value in updated_stock.items():
                        product = locked_products[product_id]
                        product.current_stock = stock_value
                        product.save(update_fields=["current_stock"])

                    sale.total = total.quantize(Decimal("0.01"))
                    sale.save(update_fields=["total"])

                    messages.success(request, "Venda registrada com sucesso.")
                    return redirect("sales-home")
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))

        feedback = self._build_feedback(form, formset)
        if feedback:
            messages.error(request, " ".join(feedback))
        else:
            messages.error(request, "Revise os dados da venda antes de finalizar.")

        return self._render(request, form, formset, products, selected_items, selected_product_ids)


class SalesHistoryView(LoginRequiredMixin, View):
    template_name = "sales/history_list.html"

    def get(self, request):
        sales_qs = Sale.objects.select_related("created_by").annotate(items_count=Count("items"))

        search_term = request.GET.get("q", "").strip()
        status_filter = request.GET.get("status", "").strip()
        start_date = request.GET.get("start_date", "").strip()
        end_date = request.GET.get("end_date", "").strip()

        if search_term:
            sales_qs = sales_qs.filter(
                Q(id__icontains=search_term)
                | Q(created_by__username__icontains=search_term)
                | Q(items__product__name__icontains=search_term)
            ).distinct()
        if status_filter:
            sales_qs = sales_qs.filter(status=status_filter)
        if start_date:
            sales_qs = sales_qs.filter(created_at__date__gte=start_date)
        if end_date:
            sales_qs = sales_qs.filter(created_at__date__lte=end_date)

        summary = sales_qs.aggregate(
            total_sales=Count("id"),
            finished_sales=Count("id", filter=Q(status=Sale.Status.FINISHED)),
            canceled_sales=Count("id", filter=Q(status=Sale.Status.CANCELED)),
            total_amount=Sum("total"),
        )

        sales_qs = sales_qs.order_by("-created_at", "-id").prefetch_related("items__product")
        paginator = Paginator(sales_qs, 8)
        page_obj = paginator.get_page(request.GET.get("page"))

        return render(
            request,
            self.template_name,
            {
                "sales": page_obj,
                "filter_state": {
                    "q": search_term,
                    "status": status_filter,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "querystring": "&".join(
                    part
                    for part in [
                        f"q={search_term}" if search_term else "",
                        f"status={status_filter}" if status_filter else "",
                        f"start_date={start_date}" if start_date else "",
                        f"end_date={end_date}" if end_date else "",
                    ]
                    if part
                ),
                "summary": {
                    "total_sales": summary["total_sales"] or 0,
                    "finished_sales": summary["finished_sales"] or 0,
                    "canceled_sales": summary["canceled_sales"] or 0,
                    "total_amount": summary["total_amount"] or Decimal("0.00"),
                },
            },
        )


class SaleDetailView(LoginRequiredMixin, View):
    template_name = "sales/history_detail.html"

    def get(self, request, pk):
        sale = get_object_or_404(
            Sale.objects.select_related("created_by").prefetch_related("items__product"),
            pk=pk,
        )
        return render(request, self.template_name, {"sale": sale})


class SaleCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            with transaction.atomic():
                sale = (
                    Sale.objects.select_for_update()
                    .select_related("created_by")
                    .prefetch_related("items__product")
                    .get(pk=pk)
                )

                if sale.status == Sale.Status.CANCELED:
                    messages.info(request, "Esta venda já estava cancelada.")
                    return redirect("sales-history-detail", pk=sale.pk)

                items = list(sale.items.select_related("product").select_for_update())
                product_ids = [item.product_id for item in items]
                products_to_update = {
                    product.pk: product
                    for product in Product.objects.select_for_update().filter(pk__in=product_ids)
                }

                for item in items:
                    product = products_to_update.get(item.product_id)
                    if product is None:
                        continue
                    product.current_stock = (product.current_stock + Decimal(item.quantity)).quantize(Decimal("0.001"))
                    product.save(update_fields=["current_stock"])

                sale.status = Sale.Status.CANCELED
                sale.save(update_fields=["status"])

                messages.success(request, "Venda cancelada e estoque devolvido com sucesso.")
                return redirect("sales-history-detail", pk=sale.pk)
        except Sale.DoesNotExist:
            messages.error(request, "Venda não encontrada.")
            return redirect("sales-history")
