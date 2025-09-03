from rest_framework import serializers
from .models import Impressora, EtiquetaLayout


class ImpressoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impressora
        fields = ['id', 'nome', 'localizacao', 'driver', 'porta', 'ativa', 'selecionada_para_impressao']


class EtiquetaLayoutListSerializer(serializers.ModelSerializer):
    """
    Serializer para a listagem de layouts. Mostra o caminho do arquivo de fonte.
    """
    class Meta:
        model = EtiquetaLayout
        # Incluímos todos os campos para a listagem
        fields = [
            'id', 'nome', 'descricao', 'largura_mm', 'altura_mm', 
            'altura_titulo_mm', 'tamanho_fonte_titulo', 'margem_vertical_qr_mm', 
            'arquivo_fonte', 'nome_fonte_reportlab', 'padrao'
        ]

class EtiquetaLayoutUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para a atualização de layouts. Torna o arquivo de fonte opcional na atualização.
    """
    # Usamos required=False para que não seja obrigatório enviar o arquivo em cada PATCH
    arquivo_fonte = serializers.FileField(required=False)

    class Meta:
        model = EtiquetaLayout
        # Incluímos todos os campos que podem ser editados
        fields = [
            'nome', 'descricao', 'largura_mm', 'altura_mm', 
            'altura_titulo_mm', 'tamanho_fonte_titulo', 'margem_vertical_qr_mm', 
            'arquivo_fonte', 'nome_fonte_reportlab', 'padrao'
        ]


class EtiquetaParaImprimirSerializer(serializers.Serializer):
    """
    Serializer para validar os dados de entrada para a impressão.
    Não está ligado a um modelo, apenas valida o payload.
    """
    titulo = serializers.CharField(max_length=200, required=True)
    url = serializers.URLField(required=True)
