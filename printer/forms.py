from django import forms
from .models import PrintServer

class PrintServerAdminForm(forms.ModelForm):
    """
    Formulário customizado para o Admin do PrintServer.
    """
    
    # 1. Este é o campo que o admin verá.
    # É um campo de senha, não obrigatório, e não renderiza o valor.
    api_key_input = forms.CharField(
        label="Chave de API",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Deixe em branco para não alterar a chave existente."
    )

    class Meta:
        model = PrintServer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 2. Se já estamos editando um objeto que TEM uma chave,
        # mostramos '********' como um placeholder para que o usuário
        # saiba que uma chave já está salva.
        if self.instance and self.instance.pk and self.instance.api_key:
            self.fields['api_key_input'].widget.attrs['placeholder'] = '********'

    def save(self, commit=True):
        # 3. Lógica de salvamento
        # Pega a chave que o usuário digitou (ex: "nova-chave-123")
        plain_key = self.cleaned_data.get('api_key_input')

        if plain_key:
            # Se o usuário digitou uma nova chave, criptografa e salva no objeto
            self.instance.set_api_key(plain_key)
        
        # 'api_key_input' não faz parte do modelo, então não tentamos
        # salvá-lo. Apenas salvamos o 'self.instance' atualizado.
        return super().save(commit=commit)