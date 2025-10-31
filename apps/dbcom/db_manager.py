import mysql.connector
from mysql.connector import errorcode
from contextlib import contextmanager
import os

class Database:
    """
    Classe principal para gerenciar a conexão e a execução de queries no MySQL.
    """
    def __init__(self):
        """
        Inicializa a configuração do banco de dados.
        Em um aplicativo real, substitua os valores 'hardcoded'
        por variáveis de ambiente (ex: os.environ.get('DB_USER')).
        """
        self.config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'user': os.environ.get('DB_USER', 'seu_usuario'),
            'password': os.environ.get('DB_PASSWORD', 'sua_senha'),
            'database': os.environ.get('DB_NAME', 'seu_banco_de_dados')
        }
        self.connection = None

    def _connect(self):
        """
        Estabelece uma conexão com o banco de dados.
        """
        try:
            # Tenta conectar usando a configuração
            self.connection = mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            # Trata erros comuns de conexão
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Erro: Usuário ou senha do banco de dados inválidos.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print(f"Erro: O banco de dados '{self.config['database']}' não existe.")
            else:
                print(f"Erro ao conectar ao MySQL: {err}")
            # Levanta a exceção para que o aplicativo saiba que a conexão falhou
            raise

    def _disconnect(self):
        """
        Fecha a conexão se estiver aberta.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None

    @contextmanager
    def get_cursor(self, dictionary=False, commit=False):
        """
        Um gerenciador de contexto para fornecer um cursor e gerenciar a transação.
        
        Args:
            dictionary (bool): Se True, o cursor retornará linhas como dicionários.
            commit (bool): Se True, a transação será commitada ao final.
        """
        self._connect()
        cursor = None
        try:
            # dictionary=True é muito útil para APIs, pois retorna {coluna: valor}
            cursor = self.connection.cursor(dictionary=dictionary)
            # Fornece o cursor para o bloco 'with'
            yield cursor
        except mysql.connector.Error as err:
            # Em caso de erro, desfaz (rollback) a transação
            print(f"Erro de banco de dados: {err}")
            if self.connection:
                self.connection.rollback()
            raise
        else:
            # Se 'commit' for True e não houver erros, commita a transação
            if commit:
                self.connection.commit()
        finally:
            # Garante que o cursor e a conexão sejam fechados
            if cursor:
                cursor.close()
            self._disconnect()

    # --- Funções Auxiliares (Opcionais, mas facilitam a vida) ---

    def fetch_query(self, query, params=None, one=False):
        """
        Executa uma query SELECT e retorna os resultados.

        Args:
            query (str): A query SQL (com %s para placeholders).
            params (tuple, optional): Os parâmetros para a query.
            one (bool, optional): Se True, retorna apenas a primeira linha (fetchone).
                                Se False, retorna todas as linhas (fetchall).

        Returns:
            list[dict] ou dict: Os resultados da query.
        """
        # dictionary=True é o padrão para fetch
        with self.get_cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            if one:
                return cursor.fetchone()
            return cursor.fetchall()

    def execute_query(self, query, params=None):
        """
        Executa uma query de modificação (INSERT, UPDATE, DELETE).

        Args:
            query (str): A query SQL (com %s para placeholders).
            params (tuple, optional): Os parâmetros para a query.

        Returns:
            int: O ID da última linha inserida (lastrowid), se aplicável.
        """
        # commit=True é essencial para queries de modificação
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or ())
            # Retorna o ID do novo registro, útil para INSERTs
            return cursor.lastrowid
