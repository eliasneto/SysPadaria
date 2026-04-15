from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category_ref", "current_stock", "min_stock", "sale_price", "is_quick_sale", "is_active")
    list_filter = ("is_active", "is_quick_sale", "category_ref")
    search_fields = ("name", "category_ref__name")
