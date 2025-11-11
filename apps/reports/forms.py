from django import forms
from django.contrib.auth.models import User
from .models import LaudoBaixa

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
