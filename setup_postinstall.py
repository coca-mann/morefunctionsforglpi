import os
import subprocess
import secrets
from django.core.management.utils import get_random_secret_key

def run_command(command, cwd):
    """Executa um comando no terminal."""
    try:
        subprocess.run(command, check=True, cwd=cwd, shell=True)
        print(f"Comando executado com sucesso: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {e}")
        # Decida se quer parar a instalação ou continuar
        # raise e 

def main():
    # O instalador nos dará o caminho de onde a aplicação foi instalada
    install_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Executando script de pós-instalação em: {install_path}")

    # 1. Gerar SECRET_KEY e criar o arquivo .env
    secret_key = get_random_secret_key()
    env_path = os.path.join(install_path, '.env')
    with open(env_path, 'w') as f:
        f.write(f"SECRET_KEY={secret_key}\n")
    print(f"Arquivo .env criado com SECRET_KEY em: {env_path}")
    
    # O comando manage.py agora precisa ser chamado pelo executável principal
    # Vamos assumir que o executável se chamará 'DirectLabelPrinter.exe'
    manage_command_prefix = [os.path.join(install_path, 'DirectLabelPrinter.exe'), 'manage']

    # 2. Executar migrações
    print("Executando migrações do banco de dados...")
    run_command(manage_command_prefix + ['migrate'], cwd=install_path)

    # 3. Criar superusuário (de forma não interativa)
    print("Criando superusuário padrão (admin/password)...")
    username = 'admin'
    email = 'admin@localhost.com'
    password = 'password' # Defina uma senha padrão inicial
    
    # Criamos um script Python temporário para isso, pois é a forma mais robusta
    create_su_script = f"""
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='{username}').exists():
    User.objects.create_superuser('{username}', '{email}', '{password}');
    print('Superusuário criado.');
else:
    print('Superusuário já existe.');
"""
    run_command(manage_command_prefix + ['shell', '-c', f'exec("""{create_su_script}""")'], cwd=install_path)

    print("Configuração inicial concluída.")


if __name__ == "__main__":
    main()