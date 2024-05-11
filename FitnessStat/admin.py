from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from tinymce.widgets import TinyMCE

from posts.models import ImagePost, Post
from users.models import User, EmailVerifications, PhoneNumberVerifySMS


class CustomAdminSite(admin.AdminSite):
    site_header = "Администрирование FitnessStat"
    side_title = "Панель управления FitnessStat"
    index_title = "Добро пожаловать в панель администратора FitnessStat"
    site_url = f"/"


custom_admin_site = CustomAdminSite(name="admin_panel")


class EmailVerificationsCustomAdmin(admin.TabularInline):
    model = EmailVerifications
    fields = ("code", "expiration")
    extra = 0


class PhoneNumberVerifySMSCustomAdmin(admin.ModelAdmin):
    list_display = ("code", "phone_number", "expiration")


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
    inlines = [EmailVerificationsCustomAdmin]


class ImagePostCustomAdmin(admin.ModelAdmin):
    """Кастомный класс админки для фотографий поста"""

    list_display = ("id",)


class PostCustomAdmin(admin.ModelAdmin):
    """Кастомный класс админки для постов"""

    list_display = (
        "id",
        "creator",
        "title",
    )
    filter_horizontal = ("images",)


custom_admin_site.register(User, UserCustomAdmin)
custom_admin_site.register(PhoneNumberVerifySMS, PhoneNumberVerifySMSCustomAdmin)
custom_admin_site.register(Group)
custom_admin_site.register(ImagePost, ImagePostCustomAdmin)
custom_admin_site.register(Post, PostCustomAdmin)
