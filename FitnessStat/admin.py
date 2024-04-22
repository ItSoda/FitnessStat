from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from tinymce.widgets import TinyMCE

from users.models import User


class CustomAdminSite(admin.AdminSite):
    site_header = "Администрирование FitnessStat"
    side_title = "Панель управления FitnessStat"
    index_title = "Добро пожаловать в панель администратора FitnessStat"
    site_url = f"/"


custom_admin_site = CustomAdminSite(name="admin_panel")


class UserCustomAdmin(admin.ModelAdmin):
    fields = (
        "photo",
        "phone_number",
        "email",
        "name",
        "login",
        "age",
        "city",
        "description",
        "experience",
        "role",
        "date_joined",
        "last_login",
        "is_verified_email",
        "is_superuser",
        "groups",
    )

    list_display = (
        "id",
        "phone_number",
        "email",
        "name",
    )
    filter_horizontal = ("groups",)
    search_fields = ["phone_number", "email", "name"]


custom_admin_site.register(User, UserCustomAdmin)
custom_admin_site.register(Group)
