from django.contrib import admin
from django.shortcuts import redirect
from .models import DashboardSettings, Display

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False if self.model.objects.exists() else True

    def changelist_view(self, request, extra_context=None):
        obj = self.model.objects.first()
        if obj:
            return redirect('admin:panel_dashboardsettings_change', obj.pk)
        return redirect('admin:panel_dashboardsettings_add')

@admin.register(Display)
class DisplayAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_screen', 'connected_at', 'last_seen')
    list_filter = ('current_screen', 'connected_at')
    search_fields = ('name',)
    readonly_fields = ('name', 'channel_name', 'available_screens', 'connected_at', 'last_seen')
    
    list_editable = ('current_screen',)

    def get_readonly_fields(self, request, obj=None):
        # Make everything readonly except current_screen, technically we only want the system to manage these
        # but the admin might want to force a screen change.
        if obj:
            return self.readonly_fields
        return self.readonly_fields