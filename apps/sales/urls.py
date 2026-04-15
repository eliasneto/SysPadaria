from django.urls import path

from .views import SaleCancelView, SaleDetailView, SalesHistoryView, SalesHomeView

urlpatterns = [
    path("", SalesHomeView.as_view(), name="sales-home"),
    path("historico/", SalesHistoryView.as_view(), name="sales-history"),
    path("historico/<int:pk>/", SaleDetailView.as_view(), name="sales-history-detail"),
    path("historico/<int:pk>/cancelar/", SaleCancelView.as_view(), name="sales-history-cancel"),
]
