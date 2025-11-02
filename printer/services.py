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
    Busca o layout padrão, GERA UM PDF DINÂMICO lendo o 'layout_json',
    imprime e descarta.
    """
    if not lista_de_etiquetas:
        return (False, "A lista de etiquetas para impressão está vazia.")

    # --- 1. BUSCAR O LAYOUT PADRÃO (Sem mudança) ---
    try:
        layout = EtiquetaLayout.objects.get(padrao=True)
    except EtiquetaLayout.DoesNotExist:
        return (False, "Nenhum Layout de Etiqueta foi definido como padrão no sistema.")
    except EtiquetaLayout.MultipleObjectsReturned:
        return (False, "ERRO: Mais de um Layout de Etiqueta está marcado como padrão.")

    # --- 2. REGISTRAR FONTE (Sem mudança) ---
    try:
        caminho_fonte = layout.arquivo_fonte.path
        pdfmetrics.registerFont(TTFont(layout.nome_fonte_reportlab, caminho_fonte))
    except Exception as e:
        return (False, f"Erro ao carregar a fonte '{layout.nome_fonte_reportlab}': {e}.")

    # --- 3. CONFIGURAÇÕES DO CANVAS (Sem mudança) ---
    LARGURA_ETIQUETA = layout.largura_mm * mm
    ALTURA_ETIQUETA = layout.altura_mm * mm
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LARGURA_ETIQUETA, ALTURA_ETIQUETA))

    print(f"Gerando {len(lista_de_etiquetas)} etiqueta(s) com o layout '{layout.nome}'...")

    # --- 4. LÓGICA DE RENDERIZAÇÃO DINÂMICA (A GRANDE MUDANÇA) ---
    
    # Pega a "receita" do JSON
    elementos_layout = layout.layout_json
    if not elementos_layout:
        return (False, f"O layout '{layout.nome}' está vazio. Adicione elementos no editor do admin.")

    # Itera sobre cada ETIQUETA a ser impressa (ex: 3 ativos = 3 páginas)
    for dados_etiqueta in lista_de_etiquetas:
        
        # Itera sobre cada ELEMENTO no layout (ex: 1 Título, 1 QR Code)
        for elemento in elementos_layout:
            
            # --- Conversão de Coordenadas ---
            # O Editor (0,0) é Topo-Esquerda
            # O ReportLab (0,0) é Baixo-Esquerda
            # Precisamos converter o Y.
            el_x = elemento.get('x', 0) * mm
            el_y_editor = elemento.get('y', 0) * mm
            
            if elemento.get('type') == 'text':
                el_h = elemento.get('height', 8) * mm
                # Posição Y do ReportLab = AlturaTotal - PosiçãoYdoEditor - AlturaDoElemento
                el_y = ALTURA_ETIQUETA - el_y_editor - el_h
                
                # Pega o dado (ex: 'titulo', 'url' ou 'custom')
                data_key = elemento.get('data_source', 'titulo')
                if data_key == 'custom':
                    texto = elemento.get('custom_text', '')
                else:
                    texto = dados_etiqueta.get(data_key, f'[{data_key}?]')
                
                # Estilos
                cor_fundo = colors.black if elemento.get('has_background') else None
                cor_texto = colors.white if elemento.get('has_background') else colors.black
                fonte = layout.nome_fonte_reportlab # Usa a fonte do layout
                tamanho_fonte = elemento.get('font_size', 12)
                
                # Desenha o fundo (se houver)
                if cor_fundo:
                    c.setFillColor(cor_fundo)
                    el_w = elemento.get('width', 40) * mm
                    c.rect(el_x, el_y, el_w, el_h, stroke=0, fill=1)
                
                # Desenha o texto
                c.setFillColor(cor_texto)
                c.setFont(fonte, tamanho_fonte)
                
                # O ReportLab desenha a partir da base. 
                # Adicionamos um pequeno ajuste (ex: 1/4 da altura) para centralizar verticalmente
                ajuste_vertical = el_h / 4 
                c.drawString(el_x, el_y + ajuste_vertical, texto)
            
            elif elemento.get('type') == 'qrcode':
                el_size = elemento.get('size', 25) * mm
                # Posição Y do ReportLab = AlturaTotal - PosiçãoYdoEditor - AlturaDoElemento
                el_y = ALTURA_ETIQUETA - el_y_editor - el_size
                
                # Pega o dado
                data_key = elemento.get('data_source', 'url')
                url = dados_etiqueta.get(data_key, '')

                # Gera o QR Code (mesma lógica sua)
                qr_maker = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
                qr_maker.add_data(url)
                qr_maker.make(fit=True)
                qr_img = qr_maker.make_image(fill_color="black", back_color="white").convert("RGB")
                
                # Desenha a imagem do QR Code
                c.drawInlineImage(qr_img, el_x, el_y, width=el_size, height=el_size)
        
        c.showPage()
    
    # --- 5. SALVAR E IMPRIMIR (Sem mudança) ---
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # O resto da sua função (criar tempfile, chamar 'imprimir_pdf_na_impressora_padrao')
    # continua EXATAMENTE IGUAL.
    
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
