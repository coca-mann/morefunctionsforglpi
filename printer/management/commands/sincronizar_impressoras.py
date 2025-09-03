from django.core.management.base import BaseCommand
from printer.models import Impressora
# Supondo que a função que criamos está em printer/utils.py
from printer.utils import capturar_dados_impressoras_windows

class Command(BaseCommand):
    help = 'Busca impressoras no sistema Windows e as cadastra ou atualiza no banco de dados.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando a sincronização de impressoras do Windows...")

        dados_das_impressoras = capturar_dados_impressoras_windows()

        if not dados_das_impressoras:
            self.stdout.write(self.style.WARNING("Nenhuma impressora encontrada no sistema."))
            return

        nomes_encontrados = []
        for dados in dados_das_impressoras:
            nome = dados.get('pPrinterName')
            if not nome:
                continue

            nomes_encontrados.append(nome)

            # Use update_or_create para inserir ou atualizar a impressora
            obj, created = Impressora.objects.update_or_create(
                nome=nome,
                defaults={
                    'driver': dados.get('pDriverName', ''),
                    'porta': dados.get('pPortName', ''),
                    'localizacao': dados.get('pLocation', ''),
                    'comentario': dados.get('pComment', ''),
                    'status_code': dados.get('Status'),
                    'attributes_code': dados.get('Attributes'),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Impressora '{nome}' cadastrada."))
            else:
                self.stdout.write(f"Impressora '{nome}' atualizada.")

        # Opcional: Desativar impressoras que estão no banco mas não foram encontradas no sistema
        Impressora.objects.exclude(nome__in=nomes_encontrados).update(ativa=False)
        self.stdout.write(self.style.WARNING("Impressoras não encontradas no sistema foram marcadas como inativas."))