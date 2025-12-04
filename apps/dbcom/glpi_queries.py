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
        LEFT JOIN glpi_tickets_users AS gtu ON gtu.tickets_id = gt.id
        LEFT JOIN glpi_users AS gu ON gu.id = gtu.users_id
        WHERE
            gt.status NOT IN (6)
            AND gt.is_deleted = 0
            AND gt.name NOT LIKE '%TECOM%'
            AND gt.name NOT LIKE '%manutenção corretiva%'
        GROUP BY
            gt.id,
            ge.name,
            gt.`date`,
            gt.status,
            gt.urgency
        ORDER BY gt.urgency DESC,
            CASE gt.status
            WHEN 1  THEN 1  -- Primeira prioridade
            WHEN 2  THEN 2  -- Segunda prioridade
            WHEN 3  THEN 3  -- Terceira prioridade
            WHEN 4 THEN 4  -- Quarta prioridade
            WHEN 10  THEN 5  -- Quinta prioridade
            WHEN 5  THEN 6  -- Sexta prioridade
            ELSE 999        -- Joga qualquer outro status (como o 4) para o final
        END ASC, gt.`date` DESC
    """
    
    return db_glpi.fetch_query(sql)


def get_assets_for_printing(asset_type: str):

    print("\n--- DEBUG: get_assets_for_printing ---")
    print(f"[DEBUG] Tentando buscar ativos do tipo: {asset_type}")

    if not db_glpi:
        print("[DEBUG] FALHA: db_glpi não está inicializado.")
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

    try:

        params = (asset_type,)
        assets = db_glpi.fetch_query(sql, params)
    
        print(f"[DEBUG] Query executada com sucesso. Itens encontrados: {len(assets)}")
        
        if len(assets) > 0:
            print(f"[DEBUG] Exemplo de ativo: {assets[0]}")
            
        return assets

    except Exception as e:
        # --- DEBUGGING ---
        # Se a query falhar (ex: tabela não existe, permissão negada na tabela)
        # o erro aparecerá aqui no console do Django.
        print(f"[DEBUG] ERRO CRÍTICO AO EXECUTAR A QUERY: {e}")
        return []


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


def get_equipamentos_para_baixa():
    """
    Simula uma query ao GLPI que retorna equipamentos com status de baixa.
    """
    if not db_glpi:
        return []
    
    sql="""
    SELECT id, name AS nome, tipo, marca, modelo, patrimonio, serie
    FROM v_equipamentos_para_baixa
    """
    
    return db_glpi.fetch_query(sql)


def get_fornecedores_glpi():
    """
    Busca os fornecedores do GLPI
    """
    if not db_glpi:
        return []
    
    sql="""
    SELECT id, name FROM glpi_suppliers WHERE is_deleted = 0 AND is_active = 1
    """

    return db_glpi.fetch_query(sql)


def get_chamados_reparo_pendentes_sql():
    """
    Busca os IDs, Nomes e Conteúdo dos chamados de reparo.
    Esta é a "Query Mestra" (Passo 2).
    """

    if not db_glpi:
        return []
    
    sql = """
        SELECT t.id, t.name, t.content 
        FROM glpi_tickets t 
        WHERE 
            ((t.name LIKE '%TECOM%') OR 
             (t.name LIKE '%manutenção corretiva%') OR 
             (t.name LIKE '%manutenção preventiva%')) 
        AND t.status IN (1, 2) 
        AND t.is_deleted = 0
        ORDER BY t.id
    """

    return db_glpi.fetch_query(sql)


def get_category_parent_id(category_id: int):
    """
    Busca o ID da categoria pai (itilcategories_id) de uma determinada categoria.
    Retorna o ID pai (int), ou 0 se for a raiz.
    """
    if not db_glpi:
        print("[DEBUG] FALHA (get_category_parent_id): db_glpi não está inicializado.")
        return None  # Retorna None para parar o loop na view

    sql = """
    SELECT ic.itilcategories_id FROM glpi_itilcategories ic WHERE ic.id = %s
    """
    params = (category_id,)

    try:
        # 'results' será uma lista, ex: [{'itilcategories_id': 140}] ou [(140,)]
        results = db_glpi.fetch_query(sql, params)

        # 1. Verifica se a query retornou algo
        if results:
            # 2. Pega a primeira linha (deve ser a única)
            first_row = results[0]
            
            # 3. Extrai o valor
            parent_id = 0 # Padrão
            
            # Se sua fetch_query retorna dicionários (ex: [{'itilcategories_id': 140}])
            if isinstance(first_row, dict):
                parent_id = first_row.get('itilcategories_id')
            # Se sua fetch_query retorna tuplas (ex: [(140,)])
            else:
                parent_id = first_row[0]
            
            # Se o ID pai for None (é a raiz), retorna 0
            if parent_id is None:
                return 0
                
            return int(parent_id)  # Retorna o NÚMERO (ex: 140)
        else:
            # Categoria não foi encontrada
            print(f"[DEBUG] Categoria ID {category_id} não encontrada no banco.")
            return None # Para o loop

    except Exception as e:
        print(f"[DEBUG] ERRO CRÍTICO AO EXECUTAR 'get_category_parent_id': {e}")
        return None  # Retorna None para parar o loop


def newpanel_dashboard_ticketcounter():
    if not db_glpi:
        return []
    
    sql="""
    SELECT
    SUM(CASE WHEN DATE(date) = CURRENT_DATE() THEN 1 ELSE 0 END) AS total_hoje,
    SUM(CASE WHEN DATE(date) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) THEN 1 ELSE 0 END) AS total_ontem,
    (SUM(CASE WHEN DATE(date) = CURRENT_DATE() THEN 1 ELSE 0 END) - 
     SUM(CASE WHEN DATE(date) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) THEN 1 ELSE 0 END)) AS diferenca
    FROM 
        glpi_tickets
    WHERE 
    is_deleted = 0
    """
        
    return db_glpi.fetch_query(sql)


def newpanel_dashboard_responsetimeavg():
    if not db_glpi:
        return []
    
    sql="""
    SELECT 
    SEC_TO_TIME(AVG(CASE WHEN DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(CURRENT_DATE(), '%Y-%m') THEN solve_delay_stat END)) AS solucao_mes_atual,
    SEC_TO_TIME(AVG(CASE WHEN DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), '%Y-%m') THEN solve_delay_stat END)) AS solucao_mes_passado,
    (AVG(CASE WHEN DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(CURRENT_DATE(), '%Y-%m') THEN solve_delay_stat END) -
     AVG(CASE WHEN DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), '%Y-%m') THEN solve_delay_stat END)) AS diferenca_segundos
    FROM 
        glpi_tickets
    WHERE 
    is_deleted = 0
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH);
    """
        
    return db_glpi.fetch_query(sql)


def newpanel_dashboard_clientsatisfactionpercent():
    if not db_glpi:
        return []
    
    sql="""
    SELECT 
    COUNT(S.id) AS qtd_pesquisas_respondidas,
    ROUND(AVG(S.satisfaction), 2) AS media_estrelas,
    ROUND((AVG(S.satisfaction) / 5) * 100, 2) AS porcentagem_satisfacao
    FROM 
        glpi_ticketsatisfactions S
    INNER JOIN 
        glpi_tickets T ON S.tickets_id = T.id
    WHERE 
    S.date_answered IS NOT NULL
    AND T.is_deleted = 0
    """
        
    return db_glpi.fetch_query(sql)


def newpanel_dashboard_departmentteam():
    if not db_glpi:
        return []
    
    sql="""
    SELECT 
    U.firstname AS nome_completo,
    U.name AS login,
    CASE 
        WHEN G.name LIKE '%Analistas%' THEN 'Analistas'
        WHEN G.name LIKE '%Técnicos%' THEN 'Técnicos'
        ELSE G.name 
    END AS grupo_perfil,
    (SELECT COUNT(DISTINCT TU.tickets_id)
     FROM glpi_tickets_users TU
     INNER JOIN glpi_tickets T ON TU.tickets_id = T.id
     WHERE TU.users_id = U.id 
       AND TU.type = 2
       AND T.is_deleted = 0
    ) AS qtd_tickets_atribuidos,
    (SELECT COUNT(P.id)
     FROM glpi_projects P
     WHERE P.is_deleted = 0
       AND (
           EXISTS (
               SELECT 1 
               FROM glpi_projectteams PT 
               WHERE PT.projects_id = P.id 
                 AND PT.itemtype = 'User' 
                 AND PT.items_id = U.id
           )
           OR 
           EXISTS (
               SELECT 1 
               FROM glpi_projecttasks PTASK
               INNER JOIN glpi_projecttaskteams PTT ON PTASK.id = PTT.projecttasks_id
               WHERE PTASK.projects_id = P.id 
                 AND PTT.itemtype = 'User' 
                 AND PTT.items_id = U.id
           )
       )
    ) AS qtd_projetos_relacionados,
    (
        IFNULL((SELECT COUNT(id) 
                FROM glpi_tickettasks 
                WHERE users_id_tech = U.id 
                  AND state = 0), 0) 
        + 
        IFNULL((SELECT COUNT(PTT.id) 
                FROM glpi_projecttaskteams PTT
                INNER JOIN glpi_projecttasks PTASK ON PTT.projecttasks_id = PTASK.id
                INNER JOIN glpi_projects PROJ ON PTASK.projects_id = PROJ.id
                WHERE PTT.itemtype = 'User' 
                  AND PTT.items_id = U.id
                  AND PROJ.projectstates_id != 3
               ), 0)
    ) AS qtd_total_tarefas
    FROM 
        glpi_users U
    INNER JOIN 
        glpi_groups_users GU ON U.id = GU.users_id
    INNER JOIN 
        glpi_groups G ON GU.groups_id = G.id
    WHERE 
        U.is_deleted = 0 
        AND U.is_active = 1
        AND (G.name LIKE '%Analistas%' OR G.name LIKE '%Técnicos%')
    ORDER BY 
    grupo_perfil, nome_completo;
    """
    
    return db_glpi.fetch_query(sql)


def newpanel_projects_data():
    if not db_glpi:
        return []
    
    sql="""
    SELECT 
    P.name AS nome_projeto,
    PS.name AS estado,
    PS.color AS cor_estado,
    CASE 
        WHEN P.users_id > 0 THEN CONCAT(U.firstname, ' ', U.realname) 
        WHEN P.groups_id > 0 THEN G.name 
        ELSE 'Não Atribuído' 
    END AS responsavel,
    SUM(CASE WHEN PT.projectstates_id = 3 THEN 1 ELSE 0 END) AS tarefas_concluidas,
    SUM(CASE WHEN PT.projectstates_id IN (2, 4) THEN 1 ELSE 0 END) AS tarefas_em_andamento,
    SUM(CASE 
        WHEN PT.id IS NOT NULL AND (PT.projectstates_id = 1) THEN 1 
        ELSE 0 
    END) AS tarefas_pendentes,
    P.percent_done AS progresso_geral_projeto,
    COALESCE(P.real_end_date, P.plan_end_date) AS data_entrega_vigente,
    P.plan_end_date AS data_planeada,
    P.real_end_date AS data_efetiva
    FROM 
        glpi_projects P
    LEFT JOIN 
        glpi_projectstates PS ON P.projectstates_id = PS.id
    LEFT JOIN 
        glpi_users U ON P.users_id = U.id
    LEFT JOIN 
        glpi_groups G ON P.groups_id = G.id
    LEFT JOIN 
        glpi_projecttasks PT ON P.id = PT.projects_id
    WHERE 
        P.is_deleted = 0 AND
        P.projectstates_id != 3
    GROUP BY 
        P.id
    ORDER BY 
    data_entrega_vigente DESC, nome_projeto;
    """
    
    return db_glpi.fetch_query(sql)


