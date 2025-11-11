from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseServerError, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from rest_framework.response import Response
from rest_framework import status
from .glpi_queries import get_assets_for_printing
from .models import GLPIConfig
from .utils import change_glpi_items_status
import json


@staff_member_required
def impressao_etiquetas_view(request):
    """
    Renderiza a página HTML personalizada para impressão de etiquetas.
    """
    
    # 2. PEGUE O CONTEXTO PADRÃO DO ADMIN
    # Isso inclui 'site_header', 'available_apps', etc.
    context = admin.site.each_context(request)
    
    # 3. DEFINA SEU CONTEÚDO CUSTOMIZADO
    tipos_de_ativos_display = [
        ('Computer', 'Computadores'),
        ('Monitor', 'Monitores'),
        ('Printer', 'Impressoras'),
        ('Phone', 'Telefones'),
        ('Networkequipment', 'Equip. de Rede'),
        ('Rack', 'Racks'),
        ('Consumableitem', 'Consumíveis'),
        ('Projetor', 'Projetores'),
        ('Scanner', 'Scanners'),
        ('Nobreak', 'Nobreaks'),
    ]

    # 4. ADICIONE SEU CONTEÚDO AO CONTEXTO PRINCIPAL
    context.update({
        'title': 'Impressão de Etiquetas de Ativos',
        'tipos_de_ativos_display': tipos_de_ativos_display,
        # 'opts' e 'app_label' não são mais necessários
        # pois o admin.site.each_context(request) já cuida disso.
    })
    
    # 5. RENDERIZE COM O CONTEXTO COMPLETO
    return render(request, 'admin/impressao_etiquetas.html', context)


@require_GET
@staff_member_required
def get_assets_data_api(request):
    """
    API interna que o JavaScript vai chamar para buscar os dados.
    """
    # ... (seu código desta view continua o mesmo)
    asset_type = request.GET.get('type')
    if not asset_type:
        return HttpResponseBadRequest("Parâmetro 'type' é obrigatório.")

    assets = get_assets_for_printing(asset_type)

    return JsonResponse(assets, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class GLPIWebhookView(View):
    
    def post(self, request, *args, **kwargs):
        
        print(f"Webhook recebido (Validação IGNORADA) de: {request.META.get('REMOTE_ADDR')}")

        try:
            config = GLPIConfig.objects.get(pk=1)
        except GLPIConfig.DoesNotExist:
            print("Erro Crítico: Configuração do GLPI (pk=1) não encontrada.")
            return HttpResponseServerError("Configuração do servidor incompleta.")

        # 1. Processar o Payload (Manual)
        body_bytes = request.body
        try:
            data = json.loads(body_bytes) 
        except json.JSONDecodeError:
            print(f"Erro: Payload recebido não é um JSON válido. Conteúdo: {body_bytes.decode('utf-8', errors='ignore')}")
            return HttpResponseBadRequest("Payload JSON inválido.")
            
        # Pega o ID do status do chamado (ex: 4)
        ticket_status_id = data.get('ticket_status')
        ticket_id = data.get('ticket_id')

        if not ticket_id or ticket_status_id is None:
            print("Payload recebido, mas sem 'ticket_id' ou 'ticket_status'.")
            return HttpResponseBadRequest("Payload incompleto.")
            
        print(f"Executando lógica para Ticket {ticket_id}. Status ID: {ticket_status_id}")

        # 2. Lógica de Decisão (CORRIGIDA)
        try:
            # Compara ID com ID (Inteiro com Inteiro)
            if (ticket_status_id == config.status_ticket_pendente_id):
                
                print(f"[Ticket {ticket_id}] Disparando Lógica de EMPRÉSTIMO.")
                change_glpi_items_status(
                    ticket_id=ticket_id,
                    new_status_id=config.status_emprestimo_id,
                    config=config
                )

            # Compara ID com ID
            elif (ticket_status_id == config.status_ticket_solucionado_id or 
                  ticket_status_id == config.status_ticket_atendimento_id):
                
                print(f"[Ticket {ticket_id}] Disparando Lógica de DEVOLUÇÃO.")
                change_glpi_items_status(
                    ticket_id=ticket_id,
                    new_status_id=config.status_operacional_id,
                    config=config,
                    check_previous_status_id=config.status_emprestimo_id
                )
            else:
                print(f"[Ticket {ticket_id}] Status ID '{ticket_status_id}' não aciona ação. Ignorando.")

        except Exception as e:
            print(f"Erro ao processar lógica para Ticket {ticket_id}: {e}")
            return HttpResponseServerError("Erro interno ao processar lógica.")

        return JsonResponse({"status": "sucesso"}, status=200)
