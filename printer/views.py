from django.http import HttpResponse
from .services import imprimir_pdf_na_impressora_padrao
import os
from django.conf import settings

def alguma_view_que_imprime(request):
    """
    Exemplo de view que aciona a impressão.
    """
    # Você só precisa do caminho do PDF que quer imprimir
    caminho_pdf = os.path.join(settings.BASE_DIR, 'caminho', 'para', 'sua', 'etiqueta.pdf')

    # A função de serviço faz todo o trabalho de encontrar a impressora certa
    sucesso, mensagem = imprimir_pdf_na_impressora_padrao(caminho_pdf)

    if sucesso:
        return HttpResponse(mensagem)
    else:
        # Retorna erro 500 (Internal Server Error) em caso de falha
        return HttpResponse(f"Falha na impressão: {mensagem}", status=500)