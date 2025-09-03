import io
import os
import win32api
import win32print
import time
import tempfile
from .models import Impressora, EtiquetaLayout
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from PIL import Image

def imprimir_pdf_na_impressora_padrao(caminho_do_pdf):
    """
    Busca a impressora padrão definida no sistema Django e envia um PDF
    diretamente para ela, usando o verbo 'printto'.

    Args:
        caminho_do_pdf (str): O caminho absoluto para o arquivo PDF no servidor.

    Returns:
        tuple: (sucesso, mensagem)
    """
    try:
        # 1. Busca a impressora selecionada no seu sistema Django
        impressora_selecionada = Impressora.objects.get(selecionada_para_impressao=True, ativa=True)
    except Impressora.DoesNotExist:
        return (False, "Nenhuma impressora padrão foi selecionada ou está ativa no sistema.")
    except Impressora.MultipleObjectsReturned:
        return (False, "ERRO CRÍTICO: Mais de uma impressora está marcada como padrão. Verifique o admin.")

    # 2. Verifica se o arquivo PDF existe
    if not os.path.exists(caminho_do_pdf):
        return (False, f"Arquivo PDF não encontrado em: {caminho_do_pdf}")

    # 3. Usa ShellExecute com 'printto' para impressão direta
    nome_da_impressora = impressora_selecionada.nome
    try:
        # Esta é a chamada mágica:
        # ShellExecute(hwnd, op, file, params, dir, show)
        # params é o nome da impressora para o verbo 'printto'
        ret = win32api.ShellExecute(
            0,                          # hwnd
            "printto",                  # Ação: imprimir para
            caminho_do_pdf,             # Arquivo
            f'"{nome_da_impressora}"',  # Parâmetro: O nome da impressora (entre aspas por segurança)
            ".",                        # Diretório
            0                           # Não mostrar a janela do aplicativo
        )

        # A API ShellExecute retorna um valor > 32 em caso de sucesso.
        if ret > 32:
            # Dê um tempo para o spooler de impressão processar
            time.sleep(5)
            return (True, f"Documento enviado diretamente para a impressora '{nome_da_impressora}'.")
        else:
            return (False, f"Falha ao enviar para a impressora via ShellExecute. Código de erro: {ret}")

    except Exception as e:
        # A exceção aqui pode vir do próprio win32api
        return (False, f"Erro na chamada da API de impressão do Windows: {e}")


def gerar_e_imprimir_etiquetas(lista_de_etiquetas: list):
    """
    Busca o layout padrão, gera um PDF com múltiplas etiquetas, imprime e descarta.
    """
    if not lista_de_etiquetas:
        return (False, "A lista de etiquetas para impressão está vazia.")

    # --- 1. BUSCAR O LAYOUT PADRÃO NO BANCO DE DADOS ---
    try:
        layout = EtiquetaLayout.objects.get(padrao=True)
    except EtiquetaLayout.DoesNotExist:
        return (False, "Nenhum Layout de Etiqueta foi definido como padrão no sistema.")
    except EtiquetaLayout.MultipleObjectsReturned:
        return (False, "ERRO: Mais de um Layout de Etiqueta está marcado como padrão.")

    # --- 2. USAR AS CONFIGURAÇÕES DO MODELO EM VEZ DE VALORES FIXOS ---
    LARGURA_ETIQUETA = layout.largura_mm * mm
    ALTURA_ETIQUETA = layout.altura_mm * mm
    MARGEM_VERTICAL_QR_INTERNA = layout.margem_vertical_qr_mm * mm
    
    try:
        # Usa o caminho do arquivo que foi feito upload
        caminho_fonte = layout.arquivo_fonte.path
        pdfmetrics.registerFont(TTFont(layout.nome_fonte_reportlab, caminho_fonte))
    except Exception as e:
        return (False, f"Erro ao carregar a fonte '{layout.nome_fonte_reportlab}': {e}.")

    # --- 3. Geração do PDF em memória (o resto do código usa as variáveis acima) ---
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LARGURA_ETIQUETA, ALTURA_ETIQUETA))

    print(f"Gerando {len(lista_de_etiquetas)} etiqueta(s) com o layout '{layout.nome}'...")
    for dados_etiqueta in lista_de_etiquetas:
        titulo = dados_etiqueta.get('titulo', 'SEM TÍTULO')
        url = dados_etiqueta.get('url', '')

        # Usa os valores do layout para o desenho
        altura_caixa_titulo = layout.altura_titulo_mm * mm
        y_caixa_titulo = ALTURA_ETIQUETA - altura_caixa_titulo
        c.setFillColor(colors.black)
        c.rect(0, y_caixa_titulo, LARGURA_ETIQUETA, altura_caixa_titulo, stroke=0, fill=1)

        c.setFillColor(colors.white)
        # Usa o nome e tamanho da fonte do layout
        c.setFont(layout.nome_fonte_reportlab, layout.tamanho_fonte_titulo)
        c.drawCentredString(LARGURA_ETIQUETA / 2, y_caixa_titulo + (altura_caixa_titulo / 4), titulo)

        # A lógica do QR Code continua a mesma, mas agora usa as variáveis do layout
        qr_maker = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
        qr_maker.add_data(url)
        qr_maker.make(fit=True)
        qr_img = qr_maker.make_image(fill_color="black", back_color="white").convert("RGB")
        
        espaco_vertical_para_qr_code = y_caixa_titulo
        altura_util_qr = espaco_vertical_para_qr_code - (MARGEM_VERTICAL_QR_INTERNA * 2)
        largura_util_qr = LARGURA_ETIQUETA
        tamanho_final_qr = min(altura_util_qr, largura_util_qr)
        y_pos_qr = MARGEM_VERTICAL_QR_INTERNA
        x_pos_qr = (LARGURA_ETIQUETA - tamanho_final_qr) / 2
        
        c.drawInlineImage(qr_img, x_pos_qr, y_pos_qr, width=tamanho_final_qr, height=tamanho_final_qr)
        
        c.showPage()
    
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # --- Processo de impressão (sem alterações) ---
    # ... (o resto da função continua exatamente igual) ...
    arquivo_temporario = None
    try:
        fd, path = tempfile.mkstemp(suffix='.pdf')
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(pdf_bytes)
        
        sucesso, mensagem = imprimir_pdf_na_impressora_padrao(path)
        if sucesso:
            mensagem = f"{len(lista_de_etiquetas)} etiqueta(s) enviada(s) com sucesso para a impressora."
        return (sucesso, mensagem)

    except Exception as e:
        return (False, f"Erro ao criar ou imprimir o arquivo com múltiplas etiquetas: {e}")
        
    finally:
        if 'path' in locals() and path and os.path.exists(path):
            os.unlink(path)
