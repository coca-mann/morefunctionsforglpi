from django.contrib import admin
from django import forms
from django.db import models
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import json
import mysql.connector
from .models import ExternalDbConfig, GLPIConfig

# --- Formulário Customizado ---
# (Este formulário é para o caso de usarmos criptografia, 
# vou mantê-lo mesmo com o modelo de texto plano por enquanto)
class ExternalDbConfigForm(forms.ModelForm):
    
    # Campo para a senha (se não estiver usando criptografia, 
    # podemos simplificar, mas vamos manter por enquanto)
    password_input = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(render_value=False),
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
class ExternalDbConfigAdmin(admin.ModelAdmin):
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


@admin.register(GLPIConfig)
class GLPIConfigAdmin(admin.ModelAdmin):
    # Atualiza o list_display com os novos campos
    list_display = ('glpi_api_url', 'glpi_app_token', 'glpi_user_token', 'status_ticket_pendente_id')
    
    fieldsets = (
        ('Configuração da API Legada (v1)', {
            'fields': (
                'glpi_api_url', 
                'glpi_app_token', 
                'glpi_user_token', 
            )
        }),
        ('Configuração do Webhook', {
            'fields': ('webhook_secret_key',)
        }),
        ('Regras de Empréstimo (IDs)', {
            'fields': (
                'status_emprestimo_id', 
                'status_operacional_id',
                'status_ticket_pendente_id', 
                'status_ticket_solucionado_id',
                'status_ticket_atendimento_id'
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
    
