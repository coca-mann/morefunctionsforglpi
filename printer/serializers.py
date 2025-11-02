from rest_framework import serializers
from .models import Impressora, EtiquetaLayout


class ImpressoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impressora
        fields = ['id', 'nome', 'localizacao', 'driver', 'porta', 'ativa', 'selecionada_para_impressao']


class EtiquetaLayoutListSerializer(serializers.ModelSerializer):
    """
    Serializer para a listagem de layouts.
    """
    class Meta:
        model = EtiquetaLayout
        # Atualize os campos
        fields = [
            'id', 'nome', 'descricao', 'largura_mm', 'altura_mm', 
            'arquivo_fonte', 'nome_fonte_reportlab', 'padrao',
            'layout_json' # Adicionado
        ]

class EtiquetaLayoutUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para a atualização de layouts.
    """
    arquivo_fonte = serializers.FileField(required=False)

    class Meta:
        model = EtiquetaLayout
        # Atualize os campos
        fields = [
            'nome', 'descricao', 'largura_mm', 'altura_mm', 
            'arquivo_fonte', 'nome_fonte_reportlab', 'padrao',
            'layout_json' # Adicionado
        ]


class EtiquetaParaImprimirSerializer(serializers.Serializer):
    """
    Serializer para validar os dados de entrada para a impressão.
    Não está ligado a um modelo, apenas valida o payload.
    """
    titulo = serializers.CharField(max_length=200, required=True)
    url = serializers.URLField(required=True)
