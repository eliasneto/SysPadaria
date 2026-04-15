from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from apps.accounts.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("", login_required(DashboardView.as_view()), name="dashboard"),
    path("contas/", include("apps.accounts.urls")),
    path("vendas/", include("apps.sales.urls")),
    path("estoque/", include("apps.inventory.urls")),
    path("financeiro/", include("apps.finance.urls")),
    path("relatorios/", include("apps.reports.urls")),
]
