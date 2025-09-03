import os
import sys
import subprocess
import secrets
from pathlib import Path

# Adiciona o diretório atual ao path para que o Django seja encontrado pelo PyInstaller
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def run_postinstall_logic():
    """
    Executa a configuração inicial. Agora que rodamos como console,
    a chamada direta ao call_command funciona perfeitamente.
    """
    print(f"Executando script de pós-instalação em: {BASE_DIR}")

    # Setup Básico do Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # <-- MUDE 'seu_projeto'
    import django
    django.setup()
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    from django.core.management.utils import get_random_secret_key

    # Gerar SECRET_KEY e criar o arquivo .env
    secret_key = get_random_secret_key()
    env_path = os.path.join(BASE_DIR, '.env')
    with open(env_path, 'w') as f:
        f.write(f"SECRET_KEY={secret_key}\n")
    print(f"Arquivo .env criado com SECRET_KEY.")

    # Garantir que as pastas existam
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    os.makedirs(BASE_DIR / 'media' / 'fonts', exist_ok=True)

    # Executar MIGRAÇÕES (agora a saída será capturada pelo instalador)
    print("Executando migrações do banco de dados...")
    try:
        # Chamada direta, sem redirecionamento de output
        call_command('migrate', interactive=False)
        print("Migrações concluídas com sucesso.")
    except Exception as e:
        print(f"ERRO CRÍTICO durante a migração: {e}")
        raise e

    # CRIAR SUPERUSUÁRIO
    print("Criando superusuário padrão (admin/password)...")
    User = get_user_model()
    username = 'admin'
    email = 'admin@localhost.com'
    password = 'password'

    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            print(f"Superusuário '{username}' criado com sucesso.")
        else:
            print(f"Superusuário '{username}' já existe, pulando criação.")
    except Exception as e:
        print(f"ERRO ao tentar criar superusuário: {e}")
        raise e

    print("Configuração inicial concluída com sucesso.")


def run_server():
    """
    Inicia o servidor web Waitress.
    """
    # Setup do Django para o servidor
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
    from core.wsgi import application 
    from waitress import serve
    
    # Garante que a pasta do banco de dados exista (redundante, mas seguro)
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    
    print("Iniciando o servidor na porta 8000...")
    serve(application, host='127.0.0.1', port=8000)


if __name__ == "__main__":
    # Verifica se um argumento especial foi passado na linha de comando
    if len(sys.argv) > 1 and sys.argv[1] == 'postinstall':
        run_postinstall_logic()
    else:
        run_server()