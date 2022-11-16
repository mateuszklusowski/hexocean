from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Tier, User, Thumbnail


class ThumbnailInline(admin.TabularInline):
    model = Tier.thumbnails.through
    extra = 1
    verbose_name = "thumbnail"


class TierAdmin(admin.ModelAdmin):
    list_display = ("name", "can_create_link")
    list_filter = ("can_create_link",)
    inlines = (ThumbnailInline,)
    exclude = ("thumbnails",)
    fieldsets = (
        (None, {"fields": ("name",)}),
        (
            _("Binary Link"),
            {"classes": ("collapse",), "fields": ("can_create_link",)},
        ),
    )


class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "tier")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("username", "tier")}),
        (
            _("Permissions"),
            {
                "classes": ("collapse",),
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "tier",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Tier, TierAdmin)
admin.site.register(Thumbnail)
