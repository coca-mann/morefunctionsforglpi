from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from .models import DashboardSettings

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    
    def get_urls(self):
        """
        Redireciona a página principal do admin (a lista)
        diretamente para a página de edição da única configuração (ID=1).
        """
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.changelist_redirect_to_change), name='settings_dashboardsettings_changelist')
        ]
        return custom_urls + urls

    def changelist_redirect_to_change(self, request):
        # Carrega (ou cria) as configurações de ID=1
        settings = DashboardSettings.objects.get_settings()
        # Redireciona para a página de 'change'
        return HttpResponseRedirect(f"../dashboardsettings/{settings.id}/change/")

    def has_add_permission(self, request):
        # Impede o usuário de clicar em "Adicionar Novo"
        return False
        
    def has_delete_permission(self, request, obj=None):
        # Impede o usuário de deletar
        return False