from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Impressora, EtiquetaLayout
from .serializers import ImpressoraSerializer, EtiquetaLayoutListSerializer, EtiquetaLayoutUpdateSerializer, EtiquetaParaImprimirSerializer
from .services import gerar_e_imprimir_etiquetas

from django.core.management import call_command
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
import io
from contextlib import redirect_stdout

# --- Views para Impressoras ---

@api_view(['GET'])
def listar_impressoras_api(request):
    """
    Retorna uma lista de todas as impressoras cadastradas no sistema.
    """
    impressoras = Impressora.objects.all()
    serializer = ImpressoraSerializer(impressoras, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def selecionar_impressora_padrao_api(request, pk):
    """
    Recebe o ID (pk) de uma impressora e a define como padrão.
    """
    try:
        impressora = Impressora.objects.get(pk=pk)
        impressora.selecionada_para_impressao = True
        impressora.save() # Nosso método save() personalizado vai desmarcar as outras
        return Response({'status': 'sucesso', 'mensagem': f"Impressora '{impressora.nome}' definida como padrão."})
    except Impressora.DoesNotExist:
        return Response({'erro': 'Impressora não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

# --- Views para Layouts ---

@api_view(['GET', 'PUT', 'PATCH'])
def detalhe_layout_api(request, pk):
    """
    Recupera, atualiza ou atualiza parcialmente um layout de etiqueta.
    """
    try:
        layout = EtiquetaLayout.objects.get(pk=pk)
    except EtiquetaLayout.DoesNotExist:
        return Response({'erro': 'Layout não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Para GET, usamos o serializer de listagem que mostra tudo
        serializer = EtiquetaLayoutListSerializer(layout)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        # Para PUT ou PATCH, usamos o serializer de atualização
        # O 'partial=True' é o que permite o PATCH (atualização parcial)
        serializer = EtiquetaLayoutUpdateSerializer(layout, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def listar_layouts_api(request):
    """
    Retorna uma lista de todos os layouts de etiqueta cadastrados.
    """
    layouts = EtiquetaLayout.objects.all()
    # Usando o novo serializer de listagem
    serializer = EtiquetaLayoutListSerializer(layouts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def selecionar_layout_padrao_api(request, pk):
    """
    Recebe o ID (pk) de um layout e o define como padrão.
    """
    try:
        layout = EtiquetaLayout.objects.get(pk=pk)
        layout.padrao = True
        layout.save() # Nosso método save() personalizado vai desmarcar os outros
        return Response({'status': 'sucesso', 'mensagem': f"Layout '{layout.nome}' definido como padrão."})
    except EtiquetaLayout.DoesNotExist:
        return Response({'erro': 'Layout não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

# --- View para Impressão ---

@api_view(['POST'])
def imprimir_etiquetas_api(request):
    """
    Recebe uma lista de objetos com 'titulo' e 'url' e os envia para impressão.
    """
    # Valida a entrada para garantir que é uma lista de objetos válidos
    serializer = EtiquetaParaImprimirSerializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Se a validação passou, chama nosso serviço
    dados_validados = serializer.validated_data
    sucesso, mensagem = gerar_e_imprimir_etiquetas(lista_de_etiquetas=dados_validados)
    
    if sucesso:
        return Response({'status': 'sucesso', 'mensagem': mensagem})
    else:
        # Erro interno do servidor (ex: impressora offline, layout não encontrado)
        return Response({'status': 'erro', 'mensagem': mensagem}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_member_required
def rodar_sincronizacao_impressoras(request):
    """
    Uma view de admin que executa o comando 'sincronizar_impressoras'
    e redireciona o usuário de volta para o admin.
    """
    
    # Usamos 'io.StringIO' para capturar qualquer saída do comando (prints, etc.)
    # e exibi-la como uma mensagem, o que é útil para feedback.
    f = io.StringIO()
    
    try:
        # 'redirect_stdout(f)' captura a saída do console
        with redirect_stdout(f):
            # Chama o seu comando pelo nome
            call_command('sincronizar_impressoras')
        
        output = f.getvalue()
        if output:
             messages.success(request, f'Sincronização concluída com sucesso! Saída: {output}')
        else:
             messages.success(request, 'Sincronização de impressoras concluída com sucesso!')

    except Exception as e:
        # Se o comando falhar, captura a exceção e mostra como erro
        messages.error(request, f'Erro ao executar a sincronização: {e}')
    
    # Redireciona o usuário de volta para a página principal do admin
    # Você pode mudar 'admin:index' para outra página se preferir
    return redirect('admin:index')