from django.urls import path

from .views import (
    CategoryDeleteView,
    CategoryUpdateView,
    InventoryMovementHistoryView,
    ProductDeleteView,
    ProductUpdateView,
    inventory_home,
)

urlpatterns = [
    path("", inventory_home, name="inventory-home"),
    path("movimentacoes/", InventoryMovementHistoryView.as_view(), name="inventory-movements"),
    path("produto/<int:pk>/editar/", ProductUpdateView.as_view(), name="inventory-product-edit"),
    path("produto/<int:pk>/excluir/", ProductDeleteView.as_view(), name="inventory-product-delete"),
    path("categoria/<int:pk>/editar/", CategoryUpdateView.as_view(), name="inventory-category-edit"),
    path("categoria/<int:pk>/excluir/", CategoryDeleteView.as_view(), name="inventory-category-delete"),
]
