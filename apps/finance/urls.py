from django.urls import path

from .views import FinanceHomeView

urlpatterns = [
    path("", FinanceHomeView.as_view(), name="finance-home"),
]
