from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import admin, messages
from django.db.models import Count, Q
from .models import (
    MotivoBaixa, LaudoBaixa, ItemLaudo, LaudoTecnico,
    ProtocoloReparo, ItemReparo, ProtocoloReparoProxy, ConfiguracaoCabecalho
)
from .forms import LaudoBaixaForm, ProtocoloReparoForm


try:
    from apps.dbcom.models import GLPIConfig
except ImportError:
    # Se falhar, o admin não funcionará, o que é esperado
    raise ImportError("Não foi possível importar 'GLPIConfig' de 'apps.dbcom.models'.")


# 1. Importe sua função de query do GLPI
try:
    from apps.dbcom.glpi_queries import get_equipamentos_para_baixa, get_chamados_reparo_pendentes_sql
    GLPI_IMPORT_DISPONIVEL = True
except ImportError:
    GLPI_IMPORT_DISPONIVEL = False

# Importa do utils (API e Parser)
try:
    from .utils import (
        get_glpi_item_details_api,    # <-- Da API
        extrair_observacao_do_ticket  # <-- Da API
    )
    GLPI_API_DISPONIVEL = True
except ImportError:
    GLPI_API_DISPONIVEL = False


# --- Funções de API e Parser (de reports.utils) ---
try:
    from .utils import (
        get_glpi_item_details_api,
        extrair_observacao_do_ticket
    )
    GLPI_REPORTS_UTILS_DISPONIVEL = True
except ImportError:
    GLPI_REPORTS_UTILS_DISPONIVEL = False

# --- Funções de SESSÃO (de dbcom.utils) (NOVO) ---
try:
    from apps.dbcom.utils import (
        get_legacy_session_token,
        kill_legacy_session
    )
    GLPI_SESSION_UTILS_DISPONIVEL = True
except ImportError:
    GLPI_SESSION_UTILS_DISPONIVEL = False


@admin.register(MotivoBaixa)
class MotivoBaixaAdmin(admin.ModelAdmin):
    """ Admin para os Motivos de Baixa. """
    list_display = ('codigo', 'titulo')
    search_fields = ('codigo', 'titulo', 'descricao')
    
    def has_module_permission(self, request):
        """ Esconde este modelo da página inicial do admin. """
        return False


class ItemLaudoInline(admin.TabularInline):
    """
    Define a visualização de 'Itens' dentro do admin do 'Laudo'.
    """
    model = ItemLaudo
    
    # Campos que aparecem no inline
    fields = (
        'nome_equipamento', 
        'tipo_equipamento', 
        'marca_equipamento', 
        'modelo_equipamento',
        'numero_patrimonio', 
        'numero_serie', 
        'motivo_baixa' # Este é o único campo editável!
    )
    
    # Campos que não podem ser editados pelo usuário no inline
    readonly_fields = (
        'nome_equipamento', 
        'tipo_equipamento', 
        'marca_equipamento', 
        'modelo_equipamento',
        'numero_patrimonio', 
        'numero_serie'
    )
    
    extra = 0 # Não mostrar formulários em branco por padrão
    can_delete = True # Permitir remover um item importado por engano
    
    def has_add_permission(self, request, obj):
        # Impede que o usuário adicione itens manualmente por este inline
        # Itens SÓ podem ser adicionados pela 'Admin Action'
        return False


@admin.register(LaudoBaixa)
class LaudoBaixaAdmin(admin.ModelAdmin):
    """ Admin principal para o Laudo de Baixa. """
    
    form = LaudoBaixaForm
    
    list_display = (
        'numero_documento', 
        'data_laudo', 
        'get_tecnico_nome_completo', 
        'destinacao', 
        'get_item_count',
        'link_imprimir_pdf'# Contagem de itens (método abaixo)
    )
    list_filter = ('data_laudo', 'tecnico_responsavel', 'destinacao')
    search_fields = ('numero_documento', 'tecnico_responsavel__username', 'itens__nome_equipamento')
    
    # Define os 'inlines'
    inlines = [ItemLaudoInline]
    
    # Ações customizadas
    actions = ['importar_itens_glpi']
    
    # Organização dos campos no formulário de edição
    fieldsets = (
        (None, {
            'fields': ('numero_documento', 'data_laudo', 'tecnico_responsavel')
        }),
        ('Destinação Final', {
            'fields': ('destinacao',)
        }),
    )
    
    # Torna o 'numero_documento' apenas leitura no formulário
    readonly_fields = ('numero_documento',)
    
    def get_queryset(self, request):
        """
        Sobrescreve o queryset principal para adicionar anotações
        que pré-calculam o status de cada laudo de uma só vez.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            # 1. Conta o total de itens
            _item_count=Count('itens', distinct=True),
            
            # 2. Conta quantos itens estão com o 'motivo_baixa' NULO (pendente)
            _missing_motivos=Count(
                'itens', 
                filter=Q(itens__motivo_baixa__isnull=True), 
                distinct=True
            )
        )
        return queryset
    
    @admin.display(
        description='Técnico Responsável', 
        ordering='tecnico_responsavel__first_name'
    )
    def get_tecnico_nome_completo(self, obj):
        # 'obj' é a instância do LaudoBaixa
        # Apenas chamamos a propriedade que já existe no models.py
        return obj.tecnico_nome_completo
    
    def link_imprimir_pdf(self, obj):
        """
        Verifica as condições antes de mostrar o link de impressão.
        Usa os valores pré-calculados do 'get_queryset'.
        """
        
        # 1. Verifica técnico
        if not obj.tecnico_responsavel:
            return "Pendente (Técnico)"

        # 2. Verifica destinação
        if not obj.destinacao:
            return "Pendente (Destinação)"
        
        # 3. Verifica se tem itens (usando a anotação)
        if obj._item_count == 0:
            return "Pendente (Sem itens)"
            
        # 4. Verifica se todos os itens têm motivo (usando a anotação)
        if obj._missing_motivos > 0:
            return f"Pendente ({obj._missing_motivos} itens sem motivo)"

        # Se todas as condições passarem:
        url = reverse('reports:gerar_pdf_laudo_baixa', args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Gerar PDF</a>')
    
    link_imprimir_pdf.short_description = "Imprimir Laudo"
    
    @admin.display(description='Qtd. Itens', ordering='_item_count')
    def get_item_count(self, obj):
        """
        Usa o valor pré-calculado '_item_count' do 'get_queryset'
        em vez de fazer uma nova query (obj.itens.count()).
        """
        return obj._item_count

    def get_actions(self, request):
        # Desabilita a ação de importação se a função não foi encontrada
        actions = super().get_actions(request)
        if not GLPI_IMPORT_DISPONIVEL:
            if 'importar_itens_glpi' in actions:
                del actions['importar_itens_glpi']
        return actions

    @admin.action(description='Importar equipamentos do GLPI para este laudo')
    def importar_itens_glpi(self, request, queryset):
        """
        Ação do Admin que busca dados no GLPI e cria os 'ItemLaudo'.
        """
        
        # 1. Validação: Ação só funciona para UM laudo de cada vez
        if queryset.count() != 1:
            self.message_user(request, 
                "Por favor, selecione apenas UM laudo para realizar a importação.", 
                messages.ERROR
            )
            return

        laudo = queryset.first()

        # 2. Executar a query do GLPI
        try:
            # Esta é a sua função!
            # Ela deve retornar uma LISTA de DICIONÁRIOS
            equipamentos_glpi = get_equipamentos_para_baixa() 
            
            if not equipamentos_glpi:
                self.message_user(request, "Nenhum equipamento encontrado no GLPI com o status de baixa.", messages.WARNING)
                return

        except Exception as e:
            self.message_user(request, f"Erro ao consultar o banco do GLPI: {e}", messages.ERROR)
            return

        # 3. Criar os objetos ItemLaudo
        itens_criados = 0
        itens_existentes = 0
        
        for equip in equipamentos_glpi:
            # 'equip' é o dicionário retornado pela sua query.
            # Ex: {'id': 123, 'nome': 'DELL-SN-12345', 'tipo': 'Computador', ...}
            # **Ajuste as chaves ('id', 'nome', etc.) para corresponder
            # ao que sua query retorna.**
            
            # get_or_create evita adicionar itens duplicados ao mesmo laudo
            obj, created = ItemLaudo.objects.get_or_create(
                laudo=laudo,
                glpi_id=equip['id'], # Chave 'id' do seu dicionário
                tipo_equipamento=equip['tipo'],
                defaults={
                    'nome_equipamento': equip['nome'],
                    'marca_equipamento': equip.get('marca', ''),
                    'modelo_equipamento': equip.get('modelo', ''),
                    'numero_patrimonio': equip.get('patrimonio', ''),
                    'numero_serie': equip.get('serie', '')
                }
            )
            
            if created:
                itens_criados += 1
            else:
                itens_existentes += 1
        
        # 4. Mensagem de sucesso
        msg = f"{itens_criados} novos itens importados para o laudo {laudo.numero_documento}. " \
              f"({itens_existentes} itens já constavam no laudo)."
        self.message_user(request, msg, messages.SUCCESS)

    def get_form(self, request, obj=None, **kwargs):
        # Coloca os campos na ordem desejada no formulário de edição
        self.fields = ('numero_documento', 'data_laudo', 'tecnico', 'destinacao_recomendada')
        return super().get_form(request, obj, **kwargs)
    
    def has_module_permission(self, request):
        """ Esconde este modelo da página inicial do admin. """
        return False


@admin.register(LaudoTecnico)
class LaudoTecnicoAdmin(admin.ModelAdmin):
    """
    Este admin 'falso' serve como o ponto de entrada no menu principal.
    Ele não tem lista de display, filtros, etc.
    Sua única função é redirecionar o usuário para a página de categorias.
    """
    
    def changelist_view(self, request, extra_context=None):
        """
        Sobrescreve a view de 'lista' (changelist) para redirecionar
        o usuário para a página de índice da sua app 'reports',
        onde está o seu template app_index.html customizado.
        """
        url = reverse('admin:app_list', kwargs={'app_label': self.model._meta.app_label})
        return HttpResponseRedirect(url)
            
    def has_module_permission(self, request):
        """ 
        Esta é a chave: esta função permite que o modelo
        seja exibido na página inicial do admin.
        """
        return True


class ItemReparoInline(admin.TabularInline):
    """
    Mostra os itens importados do GLPI dentro do Protocolo.
    """
    model = ItemReparo
    fields = (
        'glpi_ticket_id', 'tipo_equipamento_formatado', 'nome_item', 'numero_patrimonio', 'numero_serie', 
        'titulo_ticket', 'observacao_ticket'
    )
    readonly_fields = fields # Todos os campos são somente leitura
    extra = 0
    can_delete = False # Itens só são adicionados via ação

    def has_add_permission(self, request, obj):
        return False # Impede adição manual
    
    @admin.display(description="Tipo")
    def tipo_equipamento_formatado(self, obj):
        # Formata "Glpi\CustomAsset\nobreakAsset" para "Nobreak"
        if obj.glpi_item_tipo:
            return obj.glpi_item_tipo.split('\\')[-1].replace('Asset', '').upper()
        return 'N/A'


@admin.register(ProtocoloReparo)
class ProtocoloReparoAdmin(admin.ModelAdmin):
    """
    Admin principal para o Protocolo de Reparo.
    Fica "escondido" da página inicial.
    """
    form = ProtocoloReparoForm # Usa o formulário customizado
    inlines = [ItemReparoInline] # Mostra os itens dentro do protocolo
    
    list_display = (
        'numero_documento', 'data_protocolo', 'get_tecnico_nome_completo', 
        'glpi_fornecedor_nome', 'get_item_count', 'link_imprimir_pdf'
    )
    list_filter = ('data_protocolo', 'tecnico_responsavel', 'glpi_fornecedor_nome')
    search_fields = ('numero_documento', 'glpi_fornecedor_nome', 'itens__nome_item')
    readonly_fields = ('numero_documento',)
    
    actions = ['importar_chamados_glpi']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _item_count=Count('itens', distinct=True)
        )
        return queryset

    # ATUALIZADO: Otimizado para usar a anotação
    @admin.display(description='Qtd. Itens', ordering='_item_count')
    def get_item_count(self, obj):
        return obj._item_count

    def link_imprimir_pdf(self, obj):
        """
        Link condicional para gerar o PDF do Protocolo.
        """
        if obj._item_count == 0:
            return "Pendente (Sem itens)"
            
        url = reverse('reports:gerar_pdf_protocolo_reparo', args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Gerar PDF</a>')
    link_imprimir_pdf.short_description = "Imprimir Protocolo"

    @admin.display(description='Técnico Responsável', ordering='tecnico_responsavel__first_name')
    def get_tecnico_nome_completo(self, obj):
        return obj.tecnico_nome_completo
    
    @admin.action(description='[Protocolo] Importar chamados do GLPI (Próximo Lote de 10)')
    def importar_chamados_glpi(self, request, queryset):
        
        # --- Validações Iniciais ---
        if queryset.count() != 1:
            self.message_user(request, "Selecione apenas UM protocolo.", messages.ERROR)
            return
        protocolo = queryset.first()

        if not protocolo.glpi_fornecedor_id:
            self.message_user(request, f"Selecione um Fornecedor no protocolo {protocolo.numero_documento}.", messages.ERROR)
            return
        
        # Verifica se todas as nossas funções foram importadas
        if not (GLPI_IMPORT_DISPONIVEL and GLPI_API_DISPONIVEL and GLPI_SESSION_UTILS_DISPONIVEL):
            print(GLPI_API_DISPONIVEL)
            print(GLPI_IMPORT_DISPONIVEL)
            print(GLPI_SESSION_UTILS_DISPONIVEL)
            self.message_user(request, "Erro: Funções de importação (SQL, API ou Sessão) não configuradas.", messages.ERROR)
            return

        # --- Início da Lógica de Importação ---
        BATCH_SIZE = 10
        count_sucesso = 0
        count_falha_api = 0
        session_token = None # Importante para o 'finally'
        
        try:
            # 1. Pega a Configuração da API do banco
            config = GLPIConfig.objects.first()
            if not config:
                raise Exception("Configuração 'GLPIConfig' não encontrada no banco de dados.")

            # 2. Inicia a Sessão da API
            self.message_user(request, "Iniciando sessão na API do GLPI...", messages.INFO)
            session_token, error = get_legacy_session_token(config)
            if error:
                raise Exception(f"Falha ao iniciar sessão: {error}")
            
            # 3. Busca TODOS os tickets pendentes (SQL)
            todos_chamados_sql = get_chamados_reparo_pendentes_sql()
            
            # 4. Filtra os que já foram importados
            ids_ja_processados = set(
                ItemReparo.objects.filter(protocolo=protocolo).values_list('glpi_ticket_id', flat=True)
            )
            chamados_novos = [t for t in todos_chamados_sql if t['id'] not in ids_ja_processados]
            total_pendentes = len(chamados_novos)
            
            if total_pendentes == 0:
                self.message_user(request, "Nenhum chamado novo encontrado para importar.", messages.SUCCESS)
                return # Não precisa do 'finally' porque a sessão será encerrada

            # 5. Pega o Lote
            lote_atual = chamados_novos[:BATCH_SIZE]
            
            # 6. Processa o Lote
            for ticket_data in lote_atual:
                ticket_id = ticket_data['id']
                try:
                    # 7. API Calls (agora com config e session_token)
                    item_details = get_glpi_item_details_api(config, session_token, ticket_id)
                    
                    if not item_details:
                        count_falha_api += 1
                        continue 
                    print(f"\n--- DEBUG: PARSEANDO TICKET {ticket_id} ---")
                    print(ticket_data['content'])
                    print("------------------------------------------")

                    # 8. Parser de HTML
                    observacao = extrair_observacao_do_ticket(ticket_data['content'])
                    print(f"RESULTADO DO PARSER: '{observacao}'")
                    print("==========================================\n")
                    
                    # 9. Salva no Banco Django
                    ItemReparo.objects.create(
                        protocolo=protocolo,
                        glpi_ticket_id=ticket_id,
                        glpi_item_id=item_details['id_item'],
                        glpi_item_tipo=item_details['tipo_item'],
                        nome_item=item_details['nome_item'],
                        numero_serie=item_details['num_serie'],
                        numero_patrimonio=item_details['patrimonio'],
                        titulo_ticket=ticket_data['name'],
                        observacao_ticket=observacao
                    )
                    count_sucesso += 1
                
                except Exception as e_item:
                    # Captura falha em um *único* item (ex: erro 400)
                    # para não quebrar o lote inteiro.
                    print(f"Falha ao processar ticket {ticket_id}: {e_item}")
                    count_falha_api += 1
                    # Não relança a exceção, apenas registra a falha
            
            # 10. Mensagem de Feedback
            restantes = total_pendentes - count_sucesso
            msg = f"{count_sucesso} chamados importados para o {protocolo.numero_documento}. "
            if count_falha_api > 0:
                msg += f"({count_falha_api} falharam ou não tinham item). "
            if restantes > 0:
                msg += f"Restam {restantes} chamados. Execute a ação novamente."
            else:
                msg += "Importação concluída."
                
            self.message_user(request, msg, messages.SUCCESS)

        except Exception as e:
            # Captura erros "grandes" (ex: falha no initSession, falha na query SQL)
            self.message_user(request, f"Erro inesperado durante a importação: {e}", messages.ERROR)
        
        finally:
            # 11. Encerra a Sessão (SEMPRE)
            if session_token:
                self.message_user(request, "Encerrando sessão da API.", messages.INFO)
                kill_legacy_session(config, session_token)

    def get_form(self, request, obj=None, **kwargs):
        # Garante a ordem dos campos no form de edição
        self.fields = ('numero_documento', 'data_protocolo', 'tecnico_responsavel', 'glpi_fornecedor')
        return super(ProtocoloReparoAdmin, self).get_form(request, obj, **kwargs)

    def has_module_permission(self, request):
        return False # Esconde da página inicial


@admin.register(ProtocoloReparoProxy)
class ProtocoloReparoProxyAdmin(admin.ModelAdmin):
    """
    Ponto de entrada do menu principal para Protocolos de Reparo.
    """
    def changelist_view(self, request, extra_context=None):
        # Redireciona para a página de categorias da app
        url = reverse('admin:app_list', kwargs={'app_label': self.model._meta.app_label})
        return HttpResponseRedirect(url)
            
    def has_module_permission(self, request):
        return True # Mostra na página inicial


@admin.register(ConfiguracaoCabecalho)
class ConfiguracaoCabecalhoAdmin(admin.ModelAdmin):
    """
    Admin para o Singleton de Configuração de Cabeçalho.
    Redireciona o usuário da 'lista' direto para o 'formulário'.
    """
    list_display = ('nome_fantasia', 'cnpj', 'endereco_completo')
    
    def has_add_permission(self, request):
        """ Desabilita o botão 'Adicionar' se já existir um registro. """
        return not ConfiguracaoCabecalho.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """ Desabilita a ação de 'Deletar'. """
        return False

    # --- 2. ADICIONE ESTA FUNÇÃO ---
    def has_module_permission(self, request):
        """ 
        Esconde este modelo da página *principal* do admin.
        O link será colocado manualmente no 'app_index.html'.
        """
        return False

    # --- 3. ADICIONE ESTA FUNÇÃO ---
    def changelist_view(self, request, extra_context=None):
        """
        Sobrescreve a 'página de lista' (changelist) para redirecionar.
        """
        # Tenta pegar o primeiro (e único) objeto
        obj = self.model.objects.first()
        
        if obj:
            # Se o objeto existe, redireciona para a página de EDIÇÃO
            url = reverse(
                f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change',
                args=[obj.pk]
            )
        else:
            # Se não existe, redireciona para a página de ADIÇÃO
            url = reverse(
                f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add'
            )
        
        return HttpResponseRedirect(url)
