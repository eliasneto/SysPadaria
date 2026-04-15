from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ReportsHomeView(LoginRequiredMixin, TemplateView):
    template_name = "modules/placeholder.html"
    extra_context = {"title": "Relatórios"}
