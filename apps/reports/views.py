from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
# REMOVA A LINHA ABAIXO DO TOPO DO ARQUIVO:
# from weasyprint import HTML 
from .models import LaudoBaixa, MotivoBaixa
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

    # 4. Dados da sua empresa
    empresa_dados = {
        'nome': "Nome da Sua Empresa LTDA",
        'cnpj': "CNPJ: 00.000.000/0001-00",
        'endereco': "Rua Exemplo, 123, Bairro, Cidade - UF",
        'logo_url': "https://placehold.co/150x70/EFEFEF/333?text=LOGO" 
    }

    contexto = {
        'laudo': laudo,
        'itens': itens,
        'motivos_legenda': motivos_legenda,
        'empresa': empresa_dados,
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