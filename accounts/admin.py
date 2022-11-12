from django.contrib import admin
from .models import User, UserProfile
from django.contrib.auth.admin import UserAdmin

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'username', 'role', 'is_active']
    list_filter = ()
    filter_horizontal = ()
    fieldsets = ()

    list_editable = ['is_active']
admin.site.register(UserProfile)