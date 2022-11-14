from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Tier, User, Thumbnail


class ThumbnailInline(admin.TabularInline):
    model = Tier.thumbnails.through


class TierAdmin(admin.ModelAdmin):
    inlines = [
        ThumbnailInline,
    ]
    exclude = ("thumbnails",)


class UserAdmin(BaseUserAdmin):
    list_display = ("username",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("username", "tier")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
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


admin.site.register(User, UserAdmin)
admin.site.register(Tier, TierAdmin)
admin.site.register(Thumbnail)
