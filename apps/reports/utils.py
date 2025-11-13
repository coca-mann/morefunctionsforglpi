import requests
from bs4 import BeautifulSoup, NavigableString


def get_glpi_item_details_api(config, session_token, ticket_id):
    """
    Busca os detalhes de um item associado a um ticket (fluxo de 2 API calls).
    AGORA REQUER um session_token ativo.
    """
    
    # --- NOVO: Headers de Sessão ---
    # Baseado na sua função kill_legacy_session
    headers = {
        'Content-Type': 'application/json',
        'App-Token': config.glpi_app_token,
        'Session-Token': session_token 
    }
    
    try:
        base_url = config.glpi_api_url # URL base vinda do DB
        
        # 1. API Call 1: Buscar o link do item
        url_link = f"{base_url}/Ticket/{ticket_id}/Item_Ticket/"
        response_link = requests.get(url_link, headers=headers, timeout=10)
        response_link.raise_for_status() 
        
        data_link = response_link.json()
        if not data_link:
            print(f"Ticket {ticket_id}: Nenhum item associado.")
            return None
        
        item_link_info = data_link[0]
        item_href = item_link_info['links'][0]['href']
        
        # 2. API Call 2: Buscar os detalhes do item usando o href
        response_item = requests.get(item_href, headers=headers, timeout=10)
        response_item.raise_for_status()
        
        item_data = response_item.json()
        
        # 3. Montar o dicionário de retorno
        detalhes = {
            'id_item': item_data.get('id'),
            'tipo_item': item_link_info.get('itemtype'),
            'nome_item': item_data.get('name'),
            'num_serie': item_data.get('serial'),
            'patrimonio': item_data.get('otherserial')
        }
        return detalhes

    except requests.exceptions.RequestException as e:
        # O erro 400 aconteceu aqui
        print(f"Erro de API (utils.py) ao buscar item para Ticket {ticket_id}: {e}")
        # Retorna o texto do erro para o admin
        error_text = e.response.text if e.response else str(e)
        raise Exception(f"API GLPI (Ticket {ticket_id}): {error_text}")
    except (KeyError, IndexError):
        print(f"Erro de parsing (utils.py) na API para Ticket {ticket_id}")
        raise Exception(f"Erro de parsing na API (Ticket {ticket_id})")

def extrair_observacao_do_ticket(html_content):
    """
    Usa BeautifulSoup para extrair o texto de "Informações adicionais".
    VERSÃO 2.0 - Mais robusta.
    """
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Encontra a tag <b> ou <strong> que contém o texto
        tag_titulo = soup.find(lambda tag: tag.name in ('b', 'strong') and 'Informações adicionais' in tag.get_text())
        
        if not tag_titulo:
            # Não encontrou o título, então não há o que parsear
            return ""

        # 2. ESTRATÉGIA PRINCIPAL:
        # Encontra a *PRÓXIMA* tag <p> em qualquer lugar *DEPOIS* do título.
        # Isso resolve o problema de HTML malformado (como <p> dentro de <p>)
        next_p = tag_titulo.find_next('p')
        if next_p:
            texto = next_p.get_text(strip=True)
            if texto:
                return texto

        # 3. FALLBACK:
        # Se não achou <p>, talvez o texto esteja solto depois do <b>
        # Ex: <b>...adicionais:</b> Meu texto aqui <br>
        next_node = tag_titulo.next_sibling
        
        # Pula nós vazios ou que sejam apenas o ":"
        while next_node and isinstance(next_node, NavigableString) and (not next_node.strip() or next_node.strip() == ':'):
            next_node = next_node.next_sibling
            
        # Se o próximo nó for um texto, retorne-o
        if next_node and isinstance(next_node, NavigableString):
            return next_node.strip()
        
        # Se o próximo nó for outra tag (ex: <a> ou <span>), retorne o texto dela
        if next_node and next_node.name:
            return next_node.get_text(strip=True)

        return "" # Não foi possível extrair

    except Exception as e:
        print(f"Erro ao parsear HTML do ticket (utils.py): {e}")
        return ""
