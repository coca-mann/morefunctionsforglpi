import requests
import json


from django.contrib.auth.models import Group
from .glpi_queries import get_user_profiles_glpi

def sync_glpi_user_groups(user):
    """
    Sincroniza os grupos do Django do usuário com os perfis dele no GLPI.
    Garante que o usuário tenha acesso is_staff para visualizar o Django.
    """
    # 1. Tenta pegar o ID do GLPI vinculado ao usuário via SSO
    try:
        # Pega do modelo GlpiProfile (definido em apps.glpiintegrator.models)
        glpi_id = user.glpi_profile.glpi_id
    except Exception:
        # Se não houver GlpiProfile, não conseguimos buscar no banco do GLPI
        print(f"[SYNC] Usuário {user.username} não possui GlpiProfile vinculado. Pulando.")
        return

    # 2. Busca perfis no GLPI usando o ID real do usuário
    glpi_profiles = get_user_profiles_glpi(glpi_id)
    
    if not glpi_profiles:
        print(f"[SYNC] Nenhum perfil GLPI encontrado para ID {glpi_id}.")
        return

    print(f"[SYNC] Sincronizando {len(glpi_profiles)} perfis para {user.username}: {glpi_profiles}")

    # 3. Garante que os grupos existam no Django e sincroniza
    new_groups = [Group.objects.get_or_create(name=name)[0] for name in glpi_profiles]
    user.groups.set(new_groups)
    
    # 4. GARANTIA: Todo usuário que acessa via GLPI precisa ser Staff para ver o Django
    if not user.is_staff:
        user.is_staff = True
        user.save()
        print(f"[SYNC] Acesso Staff concedido automaticamente para {user.username}")


def get_legacy_session_token(config):
    """
    Inicia uma sessão na API Legada (v1) usando
    App-Token e User-Token.
    """
    print("Iniciando sessão (initSession) na API Legada...")
    
    # URL do initSession (ex: .../api.php/v1/initSession)
    url = f"{config.glpi_api_url.rstrip('/')}/initSession"
    
    headers = {
        "Content-Type": "application/json",
        "App-Token": config.glpi_app_token,
        "Authorization": f"user_token {config.glpi_user_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        session_token = data.get('session_token')
        
        if not session_token:
            print("Erro: initSession OK, mas não retornou 'session_token'.")
            return None, "Resposta do initSession não continha 'session_token'."
            
        print(f"Sessão iniciada com sucesso. Token: ...{session_token[-5:]}")
        return session_token, None 
        
    except requests.exceptions.RequestException as e:
        error_text = e.response.text if e.response else str(e)
        print(f"Falha ao iniciar sessão (initSession) em {url}: {e}")
        print(f"Resposta da API: {error_text}")
        return None, f"Falha no initSession: {error_text}"

def kill_legacy_session(config, session_token):
    """
    Encerra (killSession) uma sessão da API legada.
    """
    print(f"Encerrando sessão (killSession) ...{session_token[-5:]}")
    url = f"{config.glpi_api_url.rstrip('/')}/killSession"
    headers = {
        "Content-Type": "application/json",
        "App-Token": config.glpi_app_token,
        "Session-Token": session_token
    }
    
    try:
        requests.get(url, headers=headers)
        print("Sessão encerrada.")
    except Exception as e:
        print(f"Erro (não crítico) ao encerrar sessão: {e}")
        pass

def update_glpi_asset_status(config, session_token, itemtype, item_id, status_id):
    """
    Atualiza o status (states_id) de um ativo específico no GLPI.
    URL: apirest.php/:itemtype/:id
    """
    url = f"{config.glpi_api_url.rstrip('/')}/{itemtype}/{item_id}"
    headers = {
        "Content-Type": "application/json",
        "App-Token": config.glpi_app_token,
        "Session-Token": session_token
    }
    payload = {
        "input": {
            "states_id": status_id
        }
    }
    
    try:
        # Tenta PATCH primeiro (comum em APIs REST modernas)
        response = requests.patch(url, headers=headers, json=payload)
        
        # Se 405 (Method Not Allowed) ou 400 (dependendo da versão do GLPI), tenta PUT
        if response.status_code in [400, 405]:
            response = requests.put(url, headers=headers, json=payload)
        
        response.raise_for_status()
        return True, None
    except requests.exceptions.RequestException as e:
        error_msg = e.response.text if e.response else str(e)
        return False, error_msg

def get_oauth_token(config):
    """
    Obtém um access token da API v2.3 (OAuth2, grant 'password') usando a
    conta de serviço configurada em GLPIConfig. Token de curta duração,
    obtido uma vez por execução da ação (sem cache/refresh).
    """
    url = f"{config.glpi_api_v2_url.rstrip('/')}/token"
    data = {
        "grant_type": "password",
        "client_id": config.glpi_oauth_client_id,
        "client_secret": config.get_decrypted_oauth_client_secret(),
        "username": config.glpi_oauth_username,
        "password": config.get_decrypted_oauth_password(),
        "scope": "api",
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get('access_token')
        if not access_token:
            return None, "Resposta do /token não continha 'access_token'."

        return access_token, None

    except requests.exceptions.RequestException as e:
        error_text = e.response.text if e.response else str(e)
        return None, f"Falha ao obter token OAuth: {error_text}"


def update_glpi_asset_status_v2(config, access_token, itemtype, item_id, status_id, custom_asset=False):
    """
    Atualiza o status de um ativo via API v2.3 (OAuth2, PATCH).
    Ativos nativos: /Assets/<itemtype>/<id>, campo 'status'.
    Custom Assets:  /Assets/Custom/<itemtype>/<id>, campo 'state'.
    """
    base = config.glpi_api_v2_url.rstrip('/')
    if custom_asset:
        url = f"{base}/Assets/Custom/{itemtype}/{item_id}"
        payload = {"state": {"id": status_id}}
    else:
        url = f"{base}/Assets/{itemtype}/{item_id}"
        payload = {"status": {"id": status_id}}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return True, None
    except requests.exceptions.RequestException as e:
        error_msg = e.response.text if e.response else str(e)
        return False, error_msg


def map_django_type_to_glpi(django_type):
    """
    Mapeia os nomes amigáveis de tipos de equipamentos do Django
    para os 'itemtypes' internos do GLPI.
    """
    mapping = {
        'Computador': 'Computer',
        'Monitor': 'Monitor',
        'Impressora': 'Printer',
        'Equipamento de Rede': 'NetworkEquipment',
        'Periférico': 'Peripheral',
        'Telefone': 'Phone',
        'Nobreak': 'UninterruptiblePowerSupply', # Comum no GLPI
        'Acessório': 'Peripheral', # Ajuste conforme necessário
    }
    # Retorna o mapeamento ou o próprio tipo se não encontrar (caso já esteja no padrão GLPI)
    return mapping.get(django_type, django_type)

# --- FUNÇÃO PRINCIPAL ATUALIZADA ---
def change_glpi_items_status(ticket_id, new_status_id, config): # <-- REMOVIDO check_previous_status_id
    """
    Atualiza itens usando 100% a API LEGADA (v1).
    Esta versão FORÇA o status, ignorando o estado anterior.
    """
    
    errors = []
    session_token = None 

    try:
        session_token, error = get_legacy_session_token(config)
        if error:
            errors.append(error)
            return errors 

        action_headers = {
            "Content-Type": "application/json",
            "App-Token": config.glpi_app_token,
            "Session-Token": session_token 
        }

        get_items_url = f"{config.glpi_api_url.rstrip('/')}/Ticket/{ticket_id}/Item_Ticket/"
        
        print(f"[Ticket {ticket_id}] Buscando itens associados via API: GET {get_items_url}")

        try:
            response = requests.get(get_items_url, headers=action_headers)
            response.raise_for_status()
            items_list = response.json()
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            error_msg = f"Erro ao buscar a lista de itens (Item_Ticket): {error_text}"
            print(f"[Ticket {ticket_id}] {error_msg}")
            errors.append(error_msg)
            return errors 
        
        if not items_list:
            print(f"[Ticket {ticket_id}] Nenhum item encontrado no chamado para atualizar.")
            return errors 

        print(f"[Ticket {ticket_id}] Encontrados {len(items_list)} itens. Iniciando atualizações...")

        # 4. LOOP DE ATUALIZAÇÃO
        for item in items_list:
            item_url = None
            item_type_for_log = item.get('itemtype', 'UnknownItem')
            
            if 'links' not in item:
                print(f"[Ticket {ticket_id}] Item {item_type_for_log} (ID: {item.get('id')}) não possui 'links'. Pulando.")
                continue

            for link in item['links']:
                if link.get('rel') and link.get('rel') != 'Ticket' and link.get('href'):
                    item_url = link['href']
                    break 

            if not item_url:
                print(f"[Ticket {ticket_id}] Não foi possível encontrar o 'href' do ativo no item {item.get('id')}. Pulando.")
                continue
            
            # --- LÓGICA DE CHECAGEM (check_previous_status_id) REMOVIDA ---
            # O código agora continua direto para o PATCH/PUT
            
            # 4c. Preparar o payload e fazer o PATCH/PUT
            payload = {
                "input": {
                    "states_id": new_status_id
                }
            }
            
            print(f"\n--- DEBUG: Forçando atualização de Item (Chamada Saindo) ---")
            print(f"URL: PATCH {item_url}")
            print(f"Payload: {json.dumps(payload)}\n")
            
            try:
                response = requests.patch(item_url, headers=action_headers, json=payload)
                
                if 400 <= response.status_code < 500:
                    print(f"[Ticket {ticket_id}] PATCH falhou com {response.status_code}. Tentando PUT...")
                    response = requests.put(item_url, headers=action_headers, json=payload)

                response.raise_for_status()
                
                print(f"[Ticket {ticket_id}] Sucesso! Item {item_type_for_log} (URL: {item_url}) FORÇADO para status {new_status_id}.")

            except requests.exceptions.RequestException as e:
                error_text = e.response.text if e.response else str(e)
                error_msg = f"Erro na API! Item {item_type_for_log} (URL: {item_url}). Resposta: {error_text}"
                print(f"[Ticket {ticket_id}] {error_msg}")
                errors.append(error_msg)
        
        return errors 

    finally:
        if session_token:
            kill_legacy_session(config, session_token)

