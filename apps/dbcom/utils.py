import requests
import json
from apps.dbcom.glpi_queries import get_ticket_items 

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
    # ---------------------------------------------

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
    # ----------------------------------------------
    
    try:
        requests.get(url, headers=headers)
        print("Sessão encerrada.")
    except Exception as e:
        print(f"Erro (não crítico) ao encerrar sessão: {e}")
        pass

def change_glpi_items_status(ticket_id, new_status_id, config, check_previous_status_id=None):
    """
    Atualiza itens usando a API LEGADA (v1) com o fluxo
    correto de initSession -> Ação -> killSession.
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

        items = get_ticket_items(ticket_id)
        if not items:
            print(f"[Ticket {ticket_id}] Nenhum item encontrado para atualizar.")
            return errors 

        for item in items:
            item_type = item.get('endpoint_name')
            item_id = item.get('id')
            current_status = item.get('status_id')

            if not item_type or not item_id:
                print(f"[Ticket {ticket_id}] Item inválido na query, pulando.")
                continue
                
            if check_previous_status_id and current_status != check_previous_status_id:
                print(f"[Ticket {ticket_id}] Item {item_type} {item_id} não está no estado esperado. Ignorando devolução.")
                continue

            url = f"{config.glpi_api_url.rstrip('/')}/{item_type}/{item_id}"
            
            # --- CORREÇÃO APLICADA AQUI ---
            # O payload da API Legada DEVE estar dentro de um wrapper "input"
            payload = {
                "input": {
                    "states_id": new_status_id
                }
            }
            # -------------------------------
            
            print("\n--- DEBUG: PATCH Item (Chamada Saindo) ---")
            print(f"URL: PATCH {url}")
            print(f"Headers: {json.dumps(action_headers, indent=2)}")
            print(f"Payload: {json.dumps(payload)}") # <-- Agora imprimirá o payload correto
            print("----------------------------------------\n")
            
            try:
                response = requests.patch(url, headers=action_headers, json=payload)
                
                if 400 <= response.status_code < 500:
                    print(f"[Ticket {ticket_id}] PATCH falhou com {response.status_code}. Tentando PUT...")
                    
                    print("\n--- DEBUG: PUT Item (Chamada Saindo) ---")
                    print(f"URL: PUT {url}")
                    print(f"Headers: {json.dumps(action_headers, indent=2)}")
                    print(f"Payload: {json.dumps(payload)}")
                    print("----------------------------------------\n")
                    
                    response = requests.put(url, headers=action_headers, json=payload)

                response.raise_for_status()
                
                print(f"[Ticket {ticket_id}] Sucesso! Item {item_type} {item_id} atualizado para status {new_status_id}.")

            except requests.exceptions.RequestException as e:
                error_text = e.response.text if e.response else str(e)
                error_msg = f"Erro na API! Item {item_type} {item_id} (URL: {url}). Resposta: {error_text}"
                print(f"[Ticket {ticket_id}] {error_msg}")
                errors.append(error_msg)
        
        return errors 

    finally:
        if session_token:
            kill_legacy_session(config, session_token)
