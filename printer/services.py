import io
import os
import win32api
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
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
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

    elementos_layout = layout.layout_json
    if not elementos_layout:
        return (False, f"O layout '{layout.nome}' está vazio. Adicione elementos no editor do admin.")

    print(f"[DEBUG] Layout JSON a ser usado (total {len(elementos_layout)} elementos):")
    import json
    print(json.dumps(elementos_layout, indent=2))

    # Itera sobre cada ETIQUETA a ser impressa
    for dados_etiqueta in lista_de_etiquetas:
        
        # Itera sobre cada ELEMENTO no layout
        for elemento in elementos_layout:
            
            el_x = elemento.get('x', 0) * mm
            el_y_editor = elemento.get('y', 0) * mm
            
            if elemento.get('type') == 'text':
                # --- INÍCIO DA CORREÇÃO (Lógica de Texto Unificada) ---
                el_w = elemento.get('width', 40) * mm
                el_h = elemento.get('height', 8) * mm
                el_y = ALTURA_ETIQUETA - el_y_editor - el_h
                
                data_key = elemento.get('data_source', 'titulo')
                if data_key == 'custom':
                    texto = elemento.get('custom_text', '')
                else:
                    texto = dados_etiqueta.get(data_key, f'[{data_key}?]')
                    print(f'Titulo enviado para impressão: {texto}')
                
                # Estilos
                has_background = elemento.get('has_background', False)
                cor_fundo = colors.black if has_background else None
                cor_texto = colors.white if has_background else colors.black
                fonte = layout.nome_fonte_reportlab
                tamanho_fonte = elemento.get('font_size', 12)
                
                text_align = elemento.get('text_align', 'left')
                text_valign = elemento.get('text_valign', 'top')
                allow_wrap = elemento.get('allow_wrap', False)
                
                # Desenha o fundo (se houver)
                if cor_fundo:
                    c.setFillColor(cor_fundo)
                    c.rect(el_x, el_y, el_w, el_h, stroke=0, fill=1)

                # 1. Truncar texto manualmente se a quebra de linha estiver DESATIVADA
                if not allow_wrap:
                    text_width = pdfmetrics.stringWidth(texto, fonte, tamanho_fonte)
                    if text_width > el_w:
                        try:
                            avg_char_width = text_width / len(texto)
                            max_chars = int(el_w / avg_char_width) - 3
                            if max_chars < 1: max_chars = 1
                            texto = texto[:max_chars] + "..."
                        except ZeroDivisionError:
                            texto = "..."
                
                # 2. Definir Alinhamento Horizontal
                if text_align == 'center': align_enum = TA_CENTER
                elif text_align == 'right': align_enum = TA_RIGHT
                else: align_enum = TA_LEFT

                # 3. Criar Estilo e Parágrafo
                style = ParagraphStyle(
                    'label_text_unified',
                    fontName=fonte,
                    fontSize=tamanho_fonte,
                    textColor=cor_texto,
                    wordWrap='break' if allow_wrap else 'clip', # 'clip' para linha única
                    alignment=align_enum,
                    leading=tamanho_fonte * 1.2 # Espaço entre linhas (para quebra)
                )
                p = Paragraph(texto, style)
                
                # 4. Calcular Alinhamento Vertical
                (actual_w, actual_h) = p.wrapOn(c, el_w, el_h)
                
                y_offset = 0
                if text_valign == 'middle':
                    y_offset = (el_h - actual_h) / 2
                elif text_valign == 'top':
                    y_offset = el_h - actual_h
                # 'bottom' (padrão) tem y_offset = 0
                
                # 5. Desenhar
                c.saveState()
                path = c.beginPath()
                path.rect(el_x, el_y, el_w, el_h)
                c.clipPath(path, stroke=0, fill=0)
                
                # *** A CORREÇÃO PRINCIPAL ***
                # Desenha o parágrafo na posição X, com o ajuste Y vertical
                p.drawOn(c, el_x, el_y + y_offset)
                c.restoreState()
                
                # --- FIM DA CORREÇÃO ---
            
            elif elemento.get('type') == 'qrcode':
                # --- Lógica de QR Code (Sem mudança) ---
                el_size = elemento.get('size', 25) * mm
                el_y = ALTURA_ETIQUETA - el_y_editor - el_size
                
                data_key = elemento.get('data_source', 'url')
                if data_key == 'custom':
                    data_to_encode_raw = elemento.get('custom_text', '')
                else:
                    data_to_encode_raw = dados_etiqueta.get(data_key, '') 
                    print(f'URL qrcode enviado para impressão: {data_to_encode_raw}')

                data_to_encode = str(data_to_encode_raw).strip()

                # Use repr() para ver caracteres invisíveis como '\n' ou ' '
                print(f"[DEBUG] Tentando gerar QR Code para:")
                print(f"  > DADO BRUTO: {repr(data_to_encode_raw)}")
                print(f"  > DADO LIMPO: {repr(data_to_encode)}")
                
                has_background = elemento.get('has_background', False)
                fill_color = "white" if has_background else "black"
                back_color = "black" if has_background else "white"

                try:
                    # 3. Bloco try/except específico para o QR Code
                    qr_maker = qrcode.QRCode(
                        version=None, 
                        error_correction=qrcode.constants.ERROR_CORRECT_L, 
                        box_size=10, 
                        border=0
                    )
                    
                    qr_maker.add_data(data_to_encode) 
                    qr_maker.make(fit=True)
                    
                    qr_img = qr_maker.make_image(fill_color=fill_color, back_color=back_color)
                    
                    c.drawInlineImage(qr_img, el_x, el_y, width=el_size, height=el_size)
                
                except Exception as qr_error:
                    # 4. Se falhar, desenha um placeholder de ERRO no PDF
                    print(f"!!!!!!!!!! ERRO AO GERAR QR CODE !!!!!!!!!!")
                    print(f"  > Erro: {qr_error}")
                    print(f"  > Dados que falharam: {repr(data_to_encode)}")
                    
                    c.setFillColor(colors.red)
                    c.rect(el_x, el_y, el_size, el_size, stroke=1, fill=1)
                    c.setFillColor(colors.white)
                    c.setFont("Helvetica", 6)
                    # Tenta centralizar a palavra "ERRO"
                    try:
                        c.drawCentredString(el_x + el_size/2, el_y + el_size/2 - 3, "QR-ERROR")
                    except:
                        pass
        
        c.showPage()
    
    # --- 5. SALVAR E IMPRIMIR (Sem mudança) ---
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
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