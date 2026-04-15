from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Permissões da Padaria", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
