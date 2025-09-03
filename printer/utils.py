import win32print

def capturar_dados_impressoras_windows():
    """
    Varre o sistema Windows e retorna uma lista com os atributos detalhados
    de cada impressora instalada, usando o Level 2 de informação.
    """
    impressoras_encontradas = []
    
    # Flags para enumerar impressoras locais e conectadas
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    
    # EnumPrinters com Level 2 retorna uma tupla com (Flags, Description, Name, Comment)
    lista_impressoras = win32print.EnumPrinters(flags, None, 2)

    for impressora_info in lista_impressoras:
        nome_impressora = impressora_info['pPrinterName']
        h_printer = None
        try:
            # Abre uma conexão com a impressora para obter mais detalhes
            h_printer = win32print.OpenPrinter(nome_impressora)
            
            # GetPrinter com Level 2 retorna um dicionário com todos os detalhes
            # Esta é a chamada principal para obter os atributos
            dados_detalhados = win32print.GetPrinter(h_printer, 2)
            impressoras_encontradas.append(dados_detalhados)
            
        except Exception as e:
            print(f"Não foi possível ler os detalhes da impressora '{nome_impressora}': {e}")
            # Mesmo se GetPrinter falhar, podemos adicionar as informações básicas
            impressoras_encontradas.append(impressora_info)
            
        finally:
            if h_printer:
                win32print.ClosePrinter(h_printer)

    return impressoras_encontradas

if __name__ == '__main__':
    # Para testar a função diretamente
    dados_das_impressoras = capturar_dados_impressoras_windows()
    for dados in dados_das_impressoras:
        print("-" * 20)
        # O 'pPrinterName' é a chave principal que contém o nome
        print(f"Nome: {dados.get('pPrinterName')}")
        print(f"Porta: {dados.get('pPortName')}")
        print(f"Driver: {dados.get('pDriverName')}")
        print(f"Localização: {dados.get('pLocation')}")
        print(f"Status: {dados.get('Status')}")
        print(f"Atributos (código): {dados.get('Attributes')}")
        print(f"Comentário: {dados.get('pComment')}")