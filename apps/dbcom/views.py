from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseServerError, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.http import require_GET
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from .glpi_queries import get_assets_for_printing, get_category_parent_id
from .models import GLPIConfig, GLPIWebhook, AutomationRule
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
    
    # O 'webhook_id' vem da URL (definida em urls.py)
    def post(self, request, webhook_id, *args, **kwargs):
        
        print(f"Webhook recebido (Validação IGNORADA) no endpoint: {webhook_id}")

        try:
            config = GLPIConfig.objects.get(pk=1)
        except GLPIConfig.DoesNotExist:
            print("Erro Crítico: Configuração da API (GLPIConfig) não encontrada.")
            return HttpResponseServerError("Configuração do servidor incompleta.")

        try:
            # 1. Encontre o Webhook que recebeu a chamada
            webhook = GLPIWebhook.objects.get(id=webhook_id)
        except GLPIWebhook.DoesNotExist:
            print(f"Erro Crítico: Webhook com ID {webhook_id} não encontrado no Django.")
            return HttpResponseNotFound("Webhook não configurado.")
        
        # (Aqui você pode re-adicionar a validação HMAC usando webhook.secret_key se quiser)

        # 2. Processar o Payload
        body_bytes = request.body
        try:
            data = json.loads(body_bytes) 
        except json.JSONDecodeError:
            print(f"Erro: Payload recebido não é um JSON válido.")
            return HttpResponseBadRequest("Payload JSON inválido.")
            
        ticket_status_id = data.get('ticket_status')
        ticket_id = data.get('ticket_id')
        category_id = data.get('itilcategories_id')

        if not ticket_id or ticket_status_id is None or category_id is None:
            print("Payload incompleto. Ignorando.")
            return JsonResponse({"status": "ignorado", "motivo": "payload incompleto"}, status=200)
            
        print(f"Buscando regra para Webhook '{webhook.name}', Categoria ID: {category_id}, Status ID: {ticket_status_id}")

        # 3. Lógica de Decisão (Buscando a regra)
        rule = None
        current_category_id_to_check = category_id
        
        try:
            while current_category_id_to_check is not None and current_category_id_to_check > 0:
                print(f"...Verificando regra para Categoria ID: {current_category_id_to_check}")
                
                # A busca agora é filtrada pelo Webhook *E* pela Categoria
                rule = webhook.rules.filter(
                    trigger_category_id=current_category_id_to_check, 
                    is_active=True
                ).first()

                if rule:
                    print(f"Regra encontrada: '{rule.name}' (no nível {current_category_id_to_check})")
                    break
                
                current_category_id_to_check = get_category_parent_id(current_category_id_to_check)
            
        except Exception as e:
            print(f"Erro ao buscar regra ou categoria pai: {e}")
            return HttpResponseServerError("Erro ao processar hierarquia de regras.")
        
        if not rule:
            print(f"Nenhuma regra de automação encontrada para Categoria ID {category_id} neste webhook. Ignorando.")
            return JsonResponse({"status": "ignorado", "motivo": "sem regra"}, status=200)
        
        # 4. Executar a regra (Lógica de 'check' removida)
        all_errors = []
        try:
            solve_ids_list = [sid.strip() for sid in rule.trigger_solve_ids.split(',')]

            if (ticket_status_id == rule.trigger_pending_id):
                
                print(f"[Ticket {ticket_id}] Disparando Lógica PENDENTE: '{rule.name}'")
                all_errors = change_glpi_items_status(
                    ticket_id=ticket_id,
                    new_status_id=rule.target_asset_status_on_pending,
                    config=config
                )

            elif (str(ticket_status_id) in solve_ids_list):
                
                print(f"[Ticket {ticket_id}] Disparando Lógica SOLUCIONADO: '{rule.name}'")
                all_errors = change_glpi_items_status(
                    ticket_id=ticket_id,
                    new_status_id=rule.target_asset_status_on_solve,
                    config=config
                    # O 'check_previous_status_id' FOI REMOVIDO
                )
            else:
                print(f"[Ticket {ticket_id}] Status ID '{ticket_status_id}' não aciona ação para a regra '{rule.name}'. Ignorando.")

        except Exception as e:
            print(f"Erro GERAL ao processar lógica para Ticket {ticket_id}: {e}")
            return HttpResponseServerError(f"Erro interno geral: {e}")

        # 5. Resposta ao Webhook
        if all_errors:
            print(f"[Ticket {ticket_id}] A automação falhou. Retornando 500 para o GLPI.")
            return HttpResponseServerError(f"Falha na automação: {all_errors[0]}")
        else:
            print(f"[Ticket {ticket_id}] Automação concluída com sucesso.")
            return JsonResponse({"status": "sucesso"}, status=200)


