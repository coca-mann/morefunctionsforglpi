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


def get_assets_for_printing(asset_type: str):
    if not db_glpi:
        return []
    
    sql="""
        SELECT
        all_assets.asset_type,
        all_assets.entity,
        all_assets.asset_name,
        all_assets.url
        FROM (
            -- Computadores
            (SELECT
                'Computer' AS asset_type,
                e.name AS entity,
                c.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/computer.form.php?id=', c.id) AS url
            FROM glpi_computers c
            LEFT JOIN glpi_entities e ON e.id = c.entities_id
            WHERE c.is_template = 0 AND c.is_deleted = 0)
            UNION ALL
            -- Monitores
            (SELECT
                'Monitor' AS asset_type,
                e.name AS entity,
                m.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/monitor.form.php?id=', m.id) AS url
            FROM glpi_monitors m
            LEFT JOIN glpi_entities e ON e.id = m.entities_id
            WHERE m.is_template = 0 AND m.is_deleted = 0)
            UNION ALL
            -- Impressoras
            (SELECT
                'Printer' AS asset_type,
                e.name AS entity,
                p.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/printer.form.php?id=', p.id) AS url
            FROM glpi_printers p
            LEFT JOIN glpi_entities e ON e.id = p.entities_id
            WHERE p.is_template = 0 AND p.is_deleted = 0)
            UNION ALL
            -- Telefones
            (SELECT
                'Phone' AS asset_type,
                e.name AS entity,
                ph.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/phone.form.php?id=', ph.id) AS url
            FROM glpi_phones ph
            LEFT JOIN glpi_entities e ON e.id = ph.entities_id
            WHERE ph.is_template = 0 AND ph.is_deleted = 0)
            UNION ALL
            -- Equipamentos de Rede
            (SELECT
                'Networkequipment' AS asset_type,
                e.name AS entity,
                n.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/networkequipment.form.php?id=', n.id) AS url
            FROM glpi_networkequipments n
            LEFT JOIN glpi_entities e ON e.id = n.entities_id
            WHERE n.is_template = 0 AND n.is_deleted = 0)
            UNION ALL
            -- Racks
            (SELECT
                'Rack' AS asset_type,
                e.name AS entity,
                r.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/rack.form.php?id=', r.id) AS url
            FROM glpi_racks r
            LEFT JOIN glpi_entities e ON e.id = r.entities_id
            WHERE r.is_template = 0 AND r.is_deleted = 0)
            UNION ALL
            -- Consumíveis (Itens)
            (SELECT
                'Consumableitem' AS asset_type,
                e.name AS entity,
                ci.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/consumableitem.form.php?id=', ci.id) AS url
            FROM glpi_consumableitems ci
            LEFT JOIN glpi_entities e ON e.id = ci.entities_id
            WHERE ci.is_deleted = 0)
            UNION ALL
            -- Projetores
            SELECT 'Projetor' AS asset_type,
                glpi_locations.name AS entity,
                projetor.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/asset/asset.form.php?class=projetor&id=', projetor.id) AS url FROM glpi_assets_assets projetor
            LEFT JOIN glpi_assets_assetdefinitions ON projetor.assets_assetdefinitions_id  = glpi_assets_assetdefinitions.id
            LEFT JOIN glpi_locations ON glpi_locations.id = projetor.locations_id 
            WHERE projetor.is_template = 0 and projetor.is_deleted = 0 AND glpi_assets_assetdefinitions.system_name = 'projetor'
            UNION ALL
            -- Scanners
            SELECT 'Scanner' AS asset_type,
                glpi_locations.name AS entity,
                scanner.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/asset/asset.form.php?class=scanner&id=', scanner.id) AS url FROM glpi_assets_assets scanner
            LEFT JOIN glpi_assets_assetdefinitions ON scanner.assets_assetdefinitions_id  = glpi_assets_assetdefinitions.id
            LEFT JOIN glpi_locations ON glpi_locations.id = scanner.locations_id 
            WHERE scanner.is_template = 0 and scanner.is_deleted = 0 AND glpi_assets_assetdefinitions.system_name = 'scanner'
            UNION ALL
            -- Nobreak
            SELECT 'Nobreak' AS asset_type,
                glpi_locations.name AS entity,
                nobreak.name AS asset_name,
                CONCAT('https://centraldeservicos.grupoapariciocarvalho.com.br/front/asset/asset.form.php?class=nobreak&id=', nobreak.id) AS url FROM glpi_assets_assets nobreak
            LEFT JOIN glpi_assets_assetdefinitions ON nobreak.assets_assetdefinitions_id  = glpi_assets_assetdefinitions.id
            LEFT JOIN glpi_locations ON glpi_locations.id = nobreak.locations_id 
            WHERE nobreak.is_template = 0 and nobreak.is_deleted = 0 AND glpi_assets_assetdefinitions.system_name = 'nobreak'
        ) AS all_assets
        WHERE
            all_assets.asset_type = %s
        ORDER BY
            all_assets.asset_name ASC
    """
    params = (asset_type,)
    
    return db_glpi.fetch_query(sql, params)


def tickets_resolved_today():
    
    if not db_glpi:
        return []
    
    sql="""
    SELECT COUNT(gt.id) AS Solved_today FROM glpi_tickets gt 
    WHERE 
        gt.is_deleted = 0
        AND gt.solvedate >= CURDATE()
        AND gt.solvedate < (CURDATE() + INTERVAL 1 DAY)
    """
        
    return db_glpi.fetch_query(sql)


def tickets_open_today():
    
    if not db_glpi:
        return []
    
    sql="""
    SELECT COUNT(gt.id) AS Open_today FROM glpi_tickets gt 
    WHERE 
        gt.is_deleted = 0 
        AND gt.`date` >= CURDATE()
        AND gt.`date` < (CURDATE() + INTERVAL 1 DAY)
    """
    
    return db_glpi.fetch_query(sql)
