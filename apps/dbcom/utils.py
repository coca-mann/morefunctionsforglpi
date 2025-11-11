import requests
from datetime import datetime, timedelta
from django.utils import timezone
from apps.dbcom.glpi_queries import get_ticket_items 
# Importe o config para a função helper
from .models import GLPIConfig 

def get_glpi_token():
    """
    Busca um token de acesso OAuth2 válido, usando o cache se possível,
    ou solicitando um novo ao GLPI se expirado.
    """
    try:
        config = GLPIConfig.objects.get(pk=1)
    except GLPIConfig.DoesNotExist:
        print("Erro Crítico: Configuração do GLPI (pk=1) não encontrada.")
        return None

    # 1. Verifica se o token em cache ainda é válido
    if config.glpi_access_token and config.glpi_token_expires_at:
        # Adiciona uma margem de segurança de 60 segundos
        if config.glpi_token_expires_at > (timezone.now() + timedelta(seconds=60)):
            print("Usando token de acesso do cache.")
            return config.glpi_access_token

    # 2. Token expirado ou inexistente. Solicita um novo.
    print("Token expirado ou inexistente. Solicitando novo token...")

    token_url = f"{config.glpi_api_url.rstrip('/')}/token/"
    
    payload = {
        'grant_type': 'password',
        'client_id': config.glpi_client_id,
        'client_secret': config.glpi_client_secret,
        'username': config.glpi_api_username,
        'password': config.glpi_api_password,
        'scope': 'api' # Conforme documentação, 'api' é o escopo principal
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status() # Lança erro se a resposta for 4xx ou 5xx
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600) # (Padrão de 1 hora)

        # 3. Salva o novo token e a data de expiração no DB
        config.glpi_access_token = access_token
        config.glpi_token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))
        config.save()
        
        print("Novo token de acesso obtido e salvo.")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter token de acesso do GLPI: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        return None
    except Exception as e:
        print(f"Erro ao processar token: {e}")
        return None


def change_glpi_items_status(ticket_id, new_status_id, config, check_previous_status_id=None):
    """
    Função principal que busca itens de um chamado e atualiza seus status
    usando a API v2 com autenticação OAuth2 (Bearer Token).
    """
    
    # 1. Obter o Token de Acesso (do cache ou novo)
    access_token = get_glpi_token()
    if not access_token:
        print(f"[Ticket {ticket_id}] Falha ao obter token. Abortando.")
        return

    # 2. Busca os itens relacionados ao chamado (usando sua função de query)
    items = get_ticket_items(ticket_id)
    if not items:
        print(f"[Ticket {ticket_id}] Nenhum item encontrado para atualizar.")
        return
            
    # 3. Prepara o NOVO cabeçalho de autenticação
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
        # Os headers 'App-Token' e 'user_token' não são mais usados
    }

    # 4. Loop de atualização (lógica interna permanece a mesma)
    for item in items:
        item_type = item.get('endpoint_name') # ex: Computer, CustomAsset/Asset
        item_id = item.get('id')
        current_status = item.get('status_id')

        if not item_type or not item_id:
            print(f"[Ticket {ticket_id}] Item inválido, sem 'endpoint_name' ou 'id'.")
            continue
            
        if check_previous_status_id and current_status != check_previous_status_id:
            print(f"[Ticket {ticket_id}] Item {item_type} {item_id} não está em empréstimo. Ignorando devolução.")
            continue

        # URL da API v2 (Ex: .../api.php/v2/Computer/1)
        url = f"{config.glpi_api_url}/{item_type}/{item_id}"
        
        # O payload da v2 (com "input") já estava correto
        payload = {
            "input": {
                "states_id": new_status_id 
            }
        }
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status() # Verifica erros HTTP
            
            print(f"[Ticket {ticket_id}] Sucesso! Item {item_type} {item_id} atualizado para status {new_status_id}.")

        except requests.exceptions.RequestException as e:
            print(f"[Ticket {ticket_id}] Erro no PATCH! Item {item_type} {item_id}. Status: {e.response.status_code if e.response else 'N/A'}, Resposta: {e.response.text if e.response else e}")