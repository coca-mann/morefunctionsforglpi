from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import EtiquetaLayout, PrintServer
from .serializers import EtiquetaLayoutListSerializer, EtiquetaLayoutUpdateSerializer, EtiquetaParaImprimirSerializer
from .services import gerar_e_imprimir_etiquetas

from django.core.management import call_command
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
import io
from contextlib import redirect_stdout

import requests


@staff_member_required # Garante que apenas usuários do admin possam chamar
@api_view(['GET'])
def test_print_server_connection(request, pk):
    """
    View que o admin chama para testar a conexão com um PrintServer.
    """
    try:
        server = PrintServer.objects.get(pk=pk)
    except PrintServer.DoesNotExist:
        return Response({"mensagem": "Servidor de impressão não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    url = f"{server.endereco_servico}/api/test"
    headers = {'X-API-Key': server.get_decrypted_api_key()}

    try:
        response = requests.get(url, headers=headers, timeout=5) # Timeout de 5s
        
        if response.status_code == 200:
            return Response(response.json())
        else:
            msg = f"Serviço retornou erro {response.status_code}. Resposta: {response.text}"
            return Response({"mensagem": msg}, status=response.status_code)
            
    except requests.exceptions.Timeout:
        return Response({"mensagem": "Timeout: O serviço de impressão demorou muito para responder."}, status=status.HTTP_408_REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        return Response({"mensagem": f"Erro de Conexão: Não foi possível conectar a {server.endereco_servico}."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({"mensagem": f"Erro inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_member_required
@api_view(['GET'])
def fetch_remote_printers(request, pk):
    """
    View que o admin chama para buscar a lista de impressoras
    de um PrintServer remoto.
    """
    try:
        server = PrintServer.objects.get(pk=pk)
    except PrintServer.DoesNotExist:
        return Response({"mensagem": "Servidor de impressão não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    url = f"{server.endereco_servico}/api/printers"
    headers = {'X-API-Key': server.get_decrypted_api_key()}

    try:
        response = requests.get(url, headers=headers, timeout=10) # 10s para impressoras de rede
        
        if response.status_code == 200:
            # Re-envia a resposta JSON do serviço de impressão
            return Response(response.json())
        else:
            msg = f"Serviço retornou erro {response.status_code}. Resposta: {response.text}"
            return Response({"mensagem": msg}, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        return Response({"mensagem": f"Erro de conexão com o serviço: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# --- Views para Layouts ---

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def listar_layouts_api(request):
    """
    Retorna uma lista de todos os layouts de etiqueta cadastrados.
    """
    layouts = EtiquetaLayout.objects.all()
    # Usando o novo serializer de listagem
    serializer = EtiquetaLayoutListSerializer(layouts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated]) # Mantenha a autenticação que você preferir
def imprimir_etiquetas_api(request):
    """
    Recebe uma lista de objetos com 'titulo' e 'url' e os envia para impressão.
    AGORA LÊ O SERVIDOR ATIVO NO BANCO DE DADOS.
    """
    serializer = EtiquetaParaImprimirSerializer(data=request.data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # --- LÓGICA DE IMPRESSÃO MODIFICADA ---
    try:
        # 1. Encontra o servidor de impressão ATIVO
        server = PrintServer.objects.get(ativo=True)
    except PrintServer.DoesNotExist:
        return Response({"status": "erro", "mensagem": "Nenhum servidor de impressão está marcado como 'ativo' no admin."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except PrintServer.MultipleObjectsReturned:
        return Response({"status": "erro", "mensagem": "ERRO CRÍTICO: Mais de um servidor de impressão está 'ativo'. Verifique o admin."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not server.nome_impressora_padrao:
        return Response({"status": "erro", "mensagem": f"O servidor de impressão '{server.nome}' não tem uma impressora padrão selecionada."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 2. Chama o serviço (que agora precisa do 'server' e 'printer_name')
    dados_validados = serializer.validated_data
    sucesso, mensagem = gerar_e_imprimir_etiquetas(
        lista_de_etiquetas=dados_validados,
        print_server=server,
        printer_name=server.nome_impressora_padrao
    )
    # --- FIM DA MODIFICAÇÃO ---
    
    if sucesso:
        return Response({'status': 'sucesso', 'mensagem': mensagem})
    else:
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