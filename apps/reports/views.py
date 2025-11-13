from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
# REMOVA A LINHA ABAIXO DO TOPO DO ARQUIVO:
# from weasyprint import HTML 
from .models import LaudoBaixa, MotivoBaixa, ProtocoloReparo, ConfiguracaoCabecalho
import datetime


def gerar_pdf_laudo_baixa(request, laudo_id):
    """
    Gera um PDF para um Laudo de Baixa Patrimonial específico.
    """
    
    # ADICIONE A LINHA DE IMPORTAÇÃO AQUI DENTRO:
    try:
        from weasyprint import HTML
    except OSError:
        return HttpResponse("Erro: WeasyPrint não está instalado corretamente. Dependências do GTK3 estão faltando.", status=500)

    # 1. Buscar os dados principais
    laudo = get_object_or_404(LaudoBaixa, pk=laudo_id)
    
    # 2. Buscar os itens relacionados
    # (O resto da sua view continua exatamente igual...)
    itens = laudo.itens.all().prefetch_related('motivo_baixa').order_by('nome_equipamento')
    
    # 3. Buscar a legenda
    motivos_usados_ids = itens.values_list('motivo_baixa_id', flat=True).distinct()
    motivos_legenda = MotivoBaixa.objects.filter(id__in=motivos_usados_ids).order_by('codigo')


    config = ConfiguracaoCabecalho.objects.first()
    if not config:
        return HttpResponse("Erro: Configuração de Cabeçalho não encontrada no Admin.", status=500)

    contexto = {
        'laudo': laudo,
        'itens': itens,
        'motivos_legenda': motivos_legenda,
        'config': config,
        'data_hoje': datetime.date.today(),
    }

    # 5. Renderizar o HTML
    html_string = render_to_string(
        'reports/relatorio_laudo_baixa.html', 
        contexto
    )

    # 6. Gerar o PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # 7. Retornar a resposta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="laudo_{laudo.numero_documento}.pdf"'
    
    return response


def gerar_pdf_protocolo_reparo(request, protocolo_id):
    """
    Gera um PDF para um Protocolo de Envio para Reparo.
    """
    # 1. Buscar os dados
    protocolo = get_object_or_404(ProtocoloReparo, pk=protocolo_id)
    
    # 2. Buscar os itens relacionados
    #    Usamos 'select_related' para otimizar, mas 'itens' já está pré-buscado
    itens = protocolo.itens.all().order_by('glpi_ticket_id')

    config = ConfiguracaoCabecalho.objects.first()
    if not config:
        return HttpResponse("Erro: Configuração de Cabeçalho não encontrada no Admin.", status=500)

    # 4. Contexto para o template
    contexto = {
        'protocolo': protocolo,
        'itens': itens,
        'config': config,
        'total_itens': itens.count(),
    }

    # 5. Renderizar o HTML
    html_string = render_to_string(
        'reports/relatorio_protocolo_reparo.html', 
        contexto
    )

    # 6. Gerar o PDF (com importação 'lazy')
    try:
        from weasyprint import HTML
    except OSError:
        return HttpResponse("Erro: WeasyPrint (GTK3) não instalado no servidor.", status=500)

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # 7. Retornar a resposta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="protocolo_{protocolo.numero_documento}.pdf"'
    
    return response
