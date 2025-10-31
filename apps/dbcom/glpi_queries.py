from .db_manager import Database
from apps.dbcom.models import ExternalDbConfig

try:
    # Pega a instância da conexão "GLPI" que você cadastrou no admin
    db_glpi = Database(connection_name='GLPIDB') 
except Exception as e:
    print(f"Erro ao iniciar a conexão com GLPI: {e}")
    db_glpi = None


def get_panel_data():
    """Busca os dados para atualização do painel"""
    if not db_glpi:
        return []
    
    sql = """
        SELECT
        gt.id,
        ge.name AS 'Entidade',
        gt.name AS 'Titulo',
        DATE_FORMAT(gt.`date`, '%d/%m/%y %H:%i') AS 'Abertura',
        CASE
            WHEN gt.status = 1 THEN 'Novo'
            WHEN gt.status = 2 THEN 'Em atendimento'
            WHEN gt.status = 3 THEN 'Em atendimento (planejado)'
            WHEN gt.status = 4 THEN 'Pendente'
            WHEN gt.status = 5 THEN 'Solucionado'
            WHEN gt.status = 10 THEN 'Aprovação'
        END AS 'Status',
        CASE
            WHEN gt.urgency = 1 THEN 'Muito baixa'
            WHEN gt.urgency = 2 THEN 'Baixa'
            WHEN gt.urgency = 3 THEN 'Média'
            WHEN gt.urgency = 4 THEN 'Alta'
            WHEN gt.urgency = 5 THEN 'Muito Alta'
        END AS 'Urgencia',
        GROUP_CONCAT(
            DISTINCT CASE
                WHEN gtu.`type` = 1 THEN CONCAT_WS(' ', gu.firstname, gu.realname)
                ELSE NULL
            END
            SEPARATOR ', '
        ) AS 'Solicitante',
        GROUP_CONCAT(
            DISTINCT CASE
                WHEN gtu.`type` = 2 THEN gu.firstname
                ELSE NULL
            END
        ) AS 'Tecnico',
        gt.status AS 'idstatus'
        FROM glpi_tickets AS gt
        LEFT JOIN glpi_entities AS ge ON ge.id = gt.entities_id
        LEFT JOIN glpi_tickets_users AS gtu ON gtu.tickets_id = gt.id -- Join de usuários (1 vez)
        LEFT JOIN glpi_users AS gu ON gu.id = gtu.users_id -- Join de nomes (1 vez)
        WHERE
            gt.status NOT IN (6)
            AND gt.is_deleted = 0
        GROUP BY
            gt.id,
            ge.name,
            gt.`date`,
            gt.status,
            gt.urgency
        ORDER BY CASE gt.status
            WHEN 1  THEN 1  -- Primeira prioridade
            WHEN 2  THEN 2  -- Segunda prioridade
            WHEN 3  THEN 3  -- Terceira prioridade
            WHEN 4 THEN 4  -- Quarta prioridade
            WHEN 10  THEN 5  -- Quinta prioridade
            WHEN 5  THEN 6  -- Sexta prioridade
            ELSE 999        -- Joga qualquer outro status (como o 4) para o final
        END ASC, gt.urgency DESC
    """
    
    return db_glpi.fetch_query(sql)


def get_open_tickets():
    """Busca todos os tickets abertos (status != 'closed')."""
    if not db_glpi:
        return []

    sql = """
        SELECT id, name, date, status
        FROM glpi_tickets
        WHERE status NOT IN ('closed', 'solved')
        ORDER BY date DESC
    """
    
    # Usa a função auxiliar do db_manager
    return db_glpi.fetch_query(sql)

def get_tickets_by_user(user_email: str):
    """Busca tickets de um usuário específico."""
    if not db_glpi:
        return []

    sql = """
        SELECT t.id, t.name, u.email
        FROM glpi_tickets t
        JOIN glpi_users u ON t.users_id_recipient = u.id
        WHERE u.email = %s
    """
    
    # Passa os parâmetros de forma segura (evita SQL Injection)
    params = (user_email,)
    return db_glpi.fetch_query(sql, params)

def close_ticket(ticket_id: int):
    """Muda o status de um ticket para 'closed'."""
    if not db_glpi:
        return False
        
    sql = "UPDATE glpi_tickets SET status = 'closed' WHERE id = %s"
    params = (ticket_id,)
    
    # Usa a função auxiliar para INSERT/UPDATE
    return db_glpi.execute_query(sql, params)
