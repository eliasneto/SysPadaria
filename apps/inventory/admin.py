from django.contrib import admin

from .models import Category, InventoryMovement, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category_ref", "current_stock", "min_stock", "sale_price", "is_quick_sale", "is_active")
    list_filter = ("is_active", "is_quick_sale", "category_ref")
    search_fields = ("name", "category_ref__name")


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "movement_type", "source_product_name_snapshot", "destination_product_name_snapshot", "quantity", "created_by")
    list_filter = ("movement_type", "created_at", "created_by")
    search_fields = ("source_product_name_snapshot", "destination_product_name_snapshot", "reason", "created_by__username")
