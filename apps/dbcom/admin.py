from django.contrib import admin
from django import forms
from django.db import models
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import json
import mysql.connector
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminPasswordToggleWidget
from .models import ExternalDbConfig, GLPIConfig, AutomationRule, GLPIWebhook

# --- Formulário Customizado ---
# (Este formulário é para o caso de usarmos criptografia, 
# vou mantê-lo mesmo com o modelo de texto plano por enquanto)
class ExternalDbConfigForm(forms.ModelForm):
    
    # Campo para a senha (se não estiver usando criptografia, 
    # podemos simplificar, mas vamos manter por enquanto)
    password_input = forms.CharField(
        label="Password",
        widget=UnfoldAdminPasswordToggleWidget(render_value=False),
        required=True,
        help_text="Digite a senha do banco de dados."
    )

    class Meta:
        model = ExternalDbConfig
        fields = ['nome_conexao', 'host', 'porta', 'database', 'user', 'password_input']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se for uma edição, a senha não é obrigatória
        if self.instance and self.instance.pk:
            self.fields['password_input'].required = False
            self.fields['password_input'].help_text = "Deixe em branco para manter a senha atual. Digite uma nova senha para alterá-la."
        else:
            # Se for criação, usamos a senha do modelo (texto plano)
            # para preencher o campo se ele já existir
            if self.instance and self.instance.password:
                self.initial['password_input'] = self.instance.password


    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get('password_input')
        
        # Se o usuário digitou uma nova senha
        if raw_password:
            # No seu modelo atual (texto plano), apenas salvamos
            instance.password = raw_password
            # Se estivéssemos usando criptografia:
            # instance.set_password(raw_password)
        
        if commit:
            instance.save()
        return instance

# --- Registro do Admin ---
@admin.register(ExternalDbConfig)
class ExternalDbConfigAdmin(ModelAdmin):
    # Usa o formulário customizado
    form = ExternalDbConfigForm
    
    list_display = ('nome_conexao', 'host', 'porta', 'database', 'user')
    search_fields = ('nome_conexao', 'host', 'database')
    
    fields = ('nome_conexao', 'host', 'porta', 'database', 'user', 'password_input')
    
    # 1. CORREÇÃO: Apontar para o caminho do app 'dbcom'
    change_form_template = "admin/dbcom/externaldbconfig/change_form.html"

    # 2. Adicionar a URL de teste
    def get_urls(self):
        urls = super().get_urls()
        
        # CORREÇÃO: Mudar o nome da URL para evitar conflitos
        url_name = f"{self.model._meta.app_label}_{self.model._meta.model_name}_test_connection"
        
        custom_urls = [
            path(
                'test-connection/', 
                self.admin_site.admin_view(self.test_db_connection_view), 
                name=url_name
            ),
        ]
        return custom_urls + urls

    # 3. Criar a view de teste
    def test_db_connection_view(self, request):
        if not request.method == 'POST':
            return JsonResponse({'status': 'error', 'message': 'Apenas POST é permitido'}, status=405)

        try:
            data = json.loads(request.body)
            config = {
                'host': data.get('host'),
                'port': data.get('port'),
                'user': data.get('user'),
                'password': data.get('password'),
                'database': data.get('database'),
                'connection_timeout': 5
            }

            if not all([config['host'], config['port'], config['user'], config['database']]):
                 return JsonResponse({'status': 'error', 'message': 'Preencha todos os campos (host, porta, usuário, banco de dados)'}, status=400)

            conn = mysql.connector.connect(**config)
            conn.close()
            
            return JsonResponse({'status': 'success', 'message': 'Conexão bem-sucedida!'})

        except mysql.connector.Error as err:
            return JsonResponse({'status': 'error', 'message': f'Falha na conexão: {err}'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Dados inválidos'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Erro inesperado: {e}'}, status=500)


class GLPIConfigForm(forms.ModelForm):
    """
    Formulário customizado para o Admin do GLPIConfig: os segredos da
    conta de serviço OAuth (client secret e senha) usam campos de senha
    próprios, não vinculados diretamente ao model, e só sobrescrevem o
    valor criptografado quando o usuário digita algo novo.
    """

    glpi_oauth_client_secret_input = forms.CharField(
        label="Client Secret (OAuth)",
        widget=UnfoldAdminPasswordToggleWidget(render_value=False),
        required=False,
        help_text="Deixe em branco para manter o Client Secret atual."
    )
    glpi_oauth_password_input = forms.CharField(
        label="Senha da Conta de Serviço",
        widget=UnfoldAdminPasswordToggleWidget(render_value=False),
        required=False,
        help_text="Deixe em branco para manter a senha atual."
    )

    class Meta:
        model = GLPIConfig
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.glpi_oauth_client_secret:
            self.fields['glpi_oauth_client_secret_input'].widget.attrs['placeholder'] = '********'
        if self.instance and self.instance.pk and self.instance.glpi_oauth_password:
            self.fields['glpi_oauth_password_input'].widget.attrs['placeholder'] = '********'

    def save(self, commit=True):
        client_secret = self.cleaned_data.get('glpi_oauth_client_secret_input')
        if client_secret:
            self.instance.set_oauth_client_secret(client_secret)

        oauth_password = self.cleaned_data.get('glpi_oauth_password_input')
        if oauth_password:
            self.instance.set_oauth_password(oauth_password)

        return super().save(commit=commit)


@admin.register(GLPIConfig)
class GLPIConfigAdmin(ModelAdmin):
    form = GLPIConfigForm

    fieldsets = (
        ('Configuração da API Legada (v1)', {
            'fields': (
                'glpi_api_url',
                'glpi_app_token',
                'glpi_user_token',
                'glpi_status_baixa_id',
            )
        }),
        ('Configuração da API v2.3 (OAuth2 — conta de serviço)', {
            'fields': (
                'glpi_api_v2_url',
                'glpi_oauth_client_id',
                'glpi_oauth_client_secret_input',
                'glpi_oauth_username',
                'glpi_oauth_password_input',
            )
        }),
    )

    # --- Lógica do Singleton Admin (Permanece igual ao anterior) ---
    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        urls = [url for url in urls if url.name != f'{app_label}_{model_name}_changelist']
        custom_urls = [
            path(
                '', 
                self.admin_site.admin_view(self.changelist_view_singleton), 
                name=f'{app_label}_{model_name}_changelist' 
            )
        ]
        return custom_urls + urls

    def changelist_view_singleton(self, request, extra_context=None):
        obj = self.model.objects.first()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        if obj:
            return HttpResponseRedirect(
                reverse(f'admin:{app_label}_{model_name}_change', args=(obj.pk,))
            )
        else:
            return HttpResponseRedirect(
                reverse(f'admin:{app_label}_{model_name}_add')
            )

    def has_add_permission(self, request):
        return not self.model.objects.exists()
        
    def has_delete_permission(self, request, obj=None):
        return False
        
    def response_add(self, request, obj, post_url_continue=None):
        self.message_user(request, "Configuração criada com sucesso.")
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        return HttpResponseRedirect(
            reverse(f'admin:{app_label}_{model_name}_change', args=(obj.pk,))
        )

    def response_change(self, request, obj):
        self.message_user(request, "Configuração salva com sucesso.")
        return HttpResponseRedirect(request.path)


# Define as Regras como "linhas" dentro do Webhook
class AutomationRuleInline(TabularInline):
    model = AutomationRule
    extra = 1 # Começa com 1 linha em branco para nova regra
    fields = (
        'name', 
        'trigger_category_id', 
        'trigger_pending_id', 
        'trigger_solve_ids', 
        'target_asset_status_on_pending', 
        'target_asset_status_on_solve',
        'is_active'
    )
    verbose_name = "Regra de Automação"
    verbose_name_plural = "Regras de Automação para este Webhook"


@admin.register(GLPIWebhook)
class GLPIWebhookAdmin(ModelAdmin):
    list_display = ('name', 'id', 'get_url')
    # Mostra a URL gerada (somente leitura)
    readonly_fields = ('get_url',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'secret_key')
        }),
        ('URL (Copie e cole no GLPI)', {
            'fields': ('get_url',)
        }),
    )
    
    # Adiciona as regras na parte de baixo da página do Webhook
    inlines = [AutomationRuleInline]

