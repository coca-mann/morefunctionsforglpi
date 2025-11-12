import requests
import json


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

    # --- DEBUG: IMPRIME A REQUISIÇÃO DE SESSÃO ---
    print("\n--- DEBUG: initSession (Chamada Saindo) ---")
    print(f"URL: GET {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print("------------------------------------------\n")

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
    
    # --- DEBUG: IMPRIME A REQUISIÇÃO DE KILLSESSION ---
    print("\n--- DEBUG: killSession (Chamada Saindo) ---")
    print(f"URL: GET {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print("-------------------------------------------\n")
    
    try:
        requests.get(url, headers=headers)
        print("Sessão encerrada.")
    except Exception as e:
        print(f"Erro (não crítico) ao encerrar sessão: {e}")
        pass

# --- FUNÇÃO PRINCIPAL ATUALIZADA ---
def change_glpi_items_status(ticket_id, new_status_id, config, check_previous_status_id=None):
    """
    Atualiza itens usando 100% a API LEGADA (v1).
    Fluxo: initSession -> GET /Ticket/Item_Ticket -> (loop) -> [GET /Item] -> PATCH /Item -> killSession
    """
    
    errors = []
    session_token = None 

    try:
        # 1. OBTER O TOKEN DE SESSÃO
        session_token, error = get_legacy_session_token(config)
        if error:
            errors.append(error)
            return errors 

        # 2. PREPARAR CABEÇALHOS PARA AS AÇÕES
        action_headers = {
            "Content-Type": "application/json",
            "App-Token": config.glpi_app_token,
            "Session-Token": session_token 
        }

        # 3. BUSCAR OS ITENS ASSOCIADOS VIA API (SUA NOVA LÓGICA)
        get_items_url = f"{config.glpi_api_url.rstrip('/')}/Ticket/{ticket_id}/Item_Ticket/"
        
        print(f"[Ticket {ticket_id}] Buscando itens associados via API: GET {get_items_url}")

        try:
            response = requests.get(get_items_url, headers=action_headers)
            response.raise_for_status()
            items_list = response.json() # Recebe a lista de itens
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            error_msg = f"Erro ao buscar a lista de itens (Item_Ticket): {error_text}"
            print(f"[Ticket {ticket_id}] {error_msg}")
            errors.append(error_msg)
            return errors # Erro fatal, não podemos continuar
        
        if not items_list:
            print(f"[Ticket {ticket_id}] Nenhum item encontrado no chamado para atualizar.")
            return errors # Sucesso (lista vazia)

        print(f"[Ticket {ticket_id}] Encontrados {len(items_list)} itens. Iniciando atualizações...")

        # 4. LOOP DE ATUALIZAÇÃO
        for item in items_list:
            # 4a. Encontrar a URL correta do item no JSON de resposta
            item_url = None
            item_type_for_log = item.get('itemtype', 'UnknownItem') # Para logs de erro
            
            if 'links' not in item:
                print(f"[Ticket {ticket_id}] Item {item_type_for_log} (ID: {item.get('id')}) não possui 'links'. Pulando.")
                continue

            # Itera nos links para achar o link do ATIVO (e não o link para o Ticket)
            for link in item['links']:
                if link.get('rel') and link.get('rel') != 'Ticket' and link.get('href'):
                    item_url = link['href']
                    break # Encontramos a URL do ativo

            if not item_url:
                print(f"[Ticket {ticket_id}] Não foi possível encontrar o 'href' do ativo no item {item.get('id')}. Pulando.")
                continue
            
            # 4b. (APENAS PARA DEVOLUÇÃO) Checar o status atual do item
            if check_previous_status_id is not None:
                try:
                    print(f"[Ticket {ticket_id}] Verificando status atual de: GET {item_url}")
                    get_item_resp = requests.get(item_url, headers=action_headers)
                    get_item_resp.raise_for_status()
                    item_data = get_item_resp.json()
                    current_status = item_data.get('states_id')
                    
                    if current_status != check_previous_status_id:
                        print(f"[Ticket {ticket_id}] Item {item_type_for_log} (URL: {item_url}) não está no estado 'Em Empréstimo' ({check_previous_status_id}), está em {current_status}. Ignorando devolução.")
                        continue # Pula para o próximo item
                        
                except requests.exceptions.RequestException as e:
                    error_text = e.response.text if e.response else str(e)
                    error_msg = f"Erro ao VERIFICAR o item (GET {item_url}): {error_text}"
                    print(f"[Ticket {ticket_id}] {error_msg}")
                    errors.append(error_msg)
                    continue # Pula para o próximo item
            
            # 4c. Preparar o payload e fazer o PATCH/PUT
            payload = {
                "input": {
                    "states_id": new_status_id
                }
            }
            
            print(f"\n--- DEBUG: Atualizando Item (Chamada Saindo) ---")
            print(f"URL: PATCH {item_url}")
            print(f"Payload: {json.dumps(payload)}\n")
            
            try:
                response = requests.patch(item_url, headers=action_headers, json=payload)
                
                if 400 <= response.status_code < 500:
                    print(f"[Ticket {ticket_id}] PATCH falhou com {response.status_code}. Tentando PUT...")
                    response = requests.put(item_url, headers=action_headers, json=payload)

                response.raise_for_status()
                
                print(f"[Ticket {ticket_id}] Sucesso! Item {item_type_for_log} (URL: {item_url}) atualizado para status {new_status_id}.")

            except requests.exceptions.RequestException as e:
                error_text = e.response.text if e.response else str(e)
                error_msg = f"Erro na API! Item {item_type_for_log} (URL: {item_url}). Resposta: {error_text}"
                print(f"[Ticket {ticket_id}] {error_msg}")
                errors.append(error_msg)
        
        return errors 

    finally:
        # 5. ENCERRAR SESSÃO (SEMPRE)
        if session_token:
            kill_legacy_session(config, session_token)
