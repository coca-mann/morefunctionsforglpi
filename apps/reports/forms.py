from django import forms
from django.contrib.auth.models import User
from .models import LaudoBaixa, ProtocoloReparo


try:
    from apps.dbcom.glpi_queries import get_fornecedores_glpi
except ImportError:
    # Fallback para evitar que o Django quebre se a função não for encontrada
    def get_fornecedores_glpi():
        print("AVISO: Função 'get_fornecedores_glpi' não encontrada.")
        return []


class LaudoBaixaForm(forms.ModelForm):
    
    class Meta:
        model = LaudoBaixa
        fields = '__all__' # Deixe o Django criar os campos automaticamente

    # A customização é feita aqui:
    def __init__(self, *args, **kwargs):
        # 1. Chame o __init__ padrão primeiro
        super().__init__(*args, **kwargs)
        
        # 2. Agora, acesse o campo 'tecnico_responsavel'
        #    que o Django criou para nós
        field = self.fields['tecnico_responsavel']
        
        # 3. Ajuste o queryset (opcional, mas recomendado)
        field.queryset = User.objects.filter(
            is_staff=True, is_active=True
        ).order_by('first_name')
        
        # 4. APLIQUE A PROPRIEDADE NO LOCAL CORRETO
        field.label_from_instance = lambda obj: obj.get_full_name()


class ProtocoloReparoForm(forms.ModelForm):
    """
    Formulário customizado para Protocolos de Reparo.
    - Busca fornecedores do GLPI dinamicamente.
    - Salva o ID e o Nome do fornecedor em campos separados.
    """
    
    # 1. Campo 'falso' que não está no modelo,
    #    usado apenas para o dropdown dinâmico.
    glpi_fornecedor = forms.ChoiceField(
        label="Fornecedor (GLPI)",
        choices=[("", "---------")], # Começa vazio
        required=True,
        help_text="Lista de fornecedores ativos carregada do GLPI."
    )

    class Meta:
        model = ProtocoloReparo
        # Campos que o ModelForm vai gerenciar
        fields = ['data_protocolo', 'tecnico_responsavel']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 2. Popula o dropdown de fornecedores
        try:
            # 1. Sua função retorna a lista de dicionários (ex: [{'id': 1, 'name': 'DELL'}])
            fornecedores_glpi = get_fornecedores_glpi() 
            
            choices = [("", "---------")]
            
            # 2. Corrigimos o loop para iterar sobre a LISTA DE DICIONÁRIOS
            for fornecedor_dict in fornecedores_glpi:
                
                # 3. Acessamos os valores pelas CHAVES 'id' e 'name'
                fid = fornecedor_dict.get('id')
                fname = fornecedor_dict.get('name')
                
                if fid is not None and fname is not None:
                    # 4. Criamos o 'choice' no formato "valor|label"
                    choices.append((f"{fid}|{fname}", fname))
            
            self.fields['glpi_fornecedor'].choices = choices
        
        except Exception as e:
            # Lida com erro de conexão com o GLPI
            self.fields['glpi_fornecedor'].choices = [("", f"ERRO AO CARREGAR FORNECEDORES: {e}")]

        # 3. Customiza o campo 'tecnico_responsavel' (igual ao LaudoBaixaForm)
        field_tecnico = self.fields['tecnico_responsavel']
        field_tecnico.queryset = User.objects.filter(
            is_staff=True, is_active=True
        ).order_by('first_name', 'last_name')
        field_tecnico.label_from_instance = lambda obj: obj.get_full_name()
        
        # 4. Se estiver editando um protocolo existente, 
        #    pré-seleciona o fornecedor correto no dropdown
        if self.instance and self.instance.pk and self.instance.glpi_fornecedor_id:
            value_to_select = f"{self.instance.glpi_fornecedor_id}|{self.instance.glpi_fornecedor_nome}"
            self.fields['glpi_fornecedor'].initial = value_to_select

    def save(self, commit=True):
        # 5. Sobrescreve o 'save' para pegar o valor do campo 'falso'
        #    e salvar nos campos corretos do modelo.
        choice_data = self.cleaned_data.get('glpi_fornecedor')
        
        if choice_data:
            try:
                # Divide o valor "id|nome"
                id_str, nome = choice_data.split('|', 1)
                self.instance.glpi_fornecedor_id = int(id_str)
                self.instance.glpi_fornecedor_nome = nome
            except (ValueError, TypeError):
                # Lida com um valor inválido (ex: o "---------")
                self.instance.glpi_fornecedor_id = None
                self.instance.glpi_fornecedor_nome = None

        return super().save(commit)