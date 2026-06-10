from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ActivityLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'wallet_address', 'date_joined', 'is_active')
    search_fields = ('username', 'email', 'wallet_address')
    fieldsets     = UserAdmin.fieldsets + (
        ('Blockchain', {'fields': ('wallet_address',)}),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'action', 'success', 'ip_address', 'timestamp')
    list_filter   = ('action', 'success', 'timestamp')
    search_fields = ('user__username', 'action', 'ip_address')
    readonly_fields = ('timestamp',)