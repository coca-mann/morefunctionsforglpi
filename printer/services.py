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
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
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
    
    elementos_layout = layout.layout_json
    if not elementos_layout:
        return (False, f"O layout '{layout.nome}' está vazio. Adicione elementos no editor do admin.")

    # Itera sobre cada ETIQUETA a ser impressa
    for dados_etiqueta in lista_de_etiquetas:
        
        # Itera sobre cada ELEMENTO no layout
        for elemento in elementos_layout:
            
            el_x = elemento.get('x', 0) * mm
            el_y_editor = elemento.get('y', 0) * mm
            
            if elemento.get('type') == 'text':
                el_w = elemento.get('width', 40) * mm
                el_h = elemento.get('height', 8) * mm
                # Coordenada Y (bottom-left) da CAIXA do elemento
                el_y = ALTURA_ETIQUETA - el_y_editor - el_h
                
                data_key = elemento.get('data_source', 'titulo')
                if data_key == 'custom':
                    texto = elemento.get('custom_text', '')
                else:
                    texto = dados_etiqueta.get(data_key, f'[{data_key}?]')
                
                # Estilos
                has_background = elemento.get('has_background', False)
                cor_fundo = colors.black if has_background else None
                cor_texto = colors.white if has_background else colors.black
                fonte = layout.nome_fonte_reportlab
                tamanho_fonte = elemento.get('font_size', 12)
                
                # Desenha o fundo (se houver)
                if cor_fundo:
                    c.setFillColor(cor_fundo)
                    c.rect(el_x, el_y, el_w, el_h, stroke=0, fill=1)
                
                # --- LÓGICA DE QUEBRA DE LINHA (NOVO) ---
                allow_wrap = elemento.get('allow_wrap', False)
                
                if allow_wrap:
                    # Usa Paragraph para quebra de linha
                    style = ParagraphStyle(
                        'label_text_wrap',
                        fontName=fonte,
                        fontSize=tamanho_fonte,
                        textColor=cor_texto,
                        wordWrap='break', # Quebra palavras longas
                    )
                    p = Paragraph(texto, style)
                    p.wrapOn(c, el_w, el_h)
                    
                    # Salva o estado do canvas
                    c.saveState()
                    # Cria um "caminho de corte" (clipping path)
                    path = c.beginPath()
                    path.rect(el_x, el_y, el_w, el_h)
                    c.clipPath(path, stroke=0, fill=0)
                    
                    # Desenha o parágrafo (ele vai quebrar, mas será cortado pelo clip)
                    p.drawOn(c, el_x, el_y)
                    # Restaura o estado (remove o corte)
                    c.restoreState()
                    
                else:
                    # Usa drawString para linha única (lógica antiga com melhoria)
                    c.setFillColor(cor_texto)
                    c.setFont(fonte, tamanho_fonte)
                    
                    # Lógica de Ellipsis (...)
                    text_width = pdfmetrics.stringWidth(texto, fonte, tamanho_fonte)
                    if text_width > el_w:
                        # Trunca o texto e adiciona "..."
                        # Esta é uma aproximação, mas funcional
                        try:
                            avg_char_width = text_width / len(texto)
                            max_chars = int(el_w / avg_char_width) - 3
                            if max_chars < 1: max_chars = 1
                            texto = texto[:max_chars] + "..."
                        except ZeroDivisionError:
                            texto = "..."

                    # Centraliza verticalmente (aproximação)
                    ajuste_vertical = (el_h - tamanho_fonte) / 2
                    c.drawString(el_x, el_y + ajuste_vertical, texto)

            
            elif elemento.get('type') == 'qrcode':
                el_size = elemento.get('size', 25) * mm
                el_y = ALTURA_ETIQUETA - el_y_editor - el_size
                
                data_key = elemento.get('data_source', 'url')
                if data_key == 'custom':
                    data_to_encode = elemento.get('custom_text', '')
                else:
                    # Pega de 'dados_etiqueta' (ex: 'url' ou 'titulo')
                    data_to_encode = dados_etiqueta.get(data_key, '')

                # --- LÓGICA DE QR INVERTIDO (NOVO) ---
                has_background = elemento.get('has_background', False)
                fill_color = "white" if has_background else "black"
                back_color = "black" if has_background else "white"

                # Geração do QR Code
                qr_maker = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
                
                # Usa a variável correta
                qr_maker.add_data(data_to_encode) 
                
                qr_maker.make(fit=True)
                
                # Usa as cores corretas
                qr_img = qr_maker.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")
                
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