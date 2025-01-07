import sqlite3
import requests
import os

def criar_tabelas(db_path):
    """Cria as tabelas no banco de dados se não existirem e ajusta as tabelas existentes."""
    tabelas = {
        "CREATE_TABLE_ESTADOS": """
            CREATE TABLE IF NOT EXISTS estados (
                id INTEGER PRIMARY KEY NOT NULL, 
                nome VARCHAR(200) NOT NULL
            );
        """,
        "CREATE_TABLE_CIDADES": """
            CREATE TABLE IF NOT EXISTS cidades (
                id INTEGER PRIMARY KEY NOT NULL, 
                codigo_igbe VARCHAR(200) NOT NULL,
                nome VARCHAR(200) NOT NULL
            );
        """,
        "CREATE_TABLE_ENTIDADE": """
            CREATE TABLE IF NOT EXISTS entidades (
                id INTEGER PRIMARY KEY NOT NULL, 
                codigo_igbe VARCHAR(200) NOT NULL,
                nome VARCHAR(200) NOT NULL,
                entidade_id INTEGER NOT NULL
            );
        """,
    }

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for tabela_nome, tabela_sql in tabelas.items():
                # print(f"[INFO] Criando ou ajustando tabela: {tabela_nome}")
                cursor.execute(tabela_sql)

            # Verificar e adicionar a coluna `entidade_id` na tabela `entidades`, se necessário
            cursor.execute("PRAGMA table_info(entidades)")
            colunas = [info[1] for info in cursor.fetchall()]
            if "entidade_id" not in colunas:
                # print("[INFO] Adicionando coluna 'entidade_id' na tabela 'entidades'.")
                cursor.execute("ALTER TABLE entidades ADD COLUMN entidade_id INTEGER NOT NULL DEFAULT 0")

            conn.commit()
    #         print("[INFO] Tabelas criadas ou ajustadas com sucesso.")
    except sqlite3.Error as e:
        print(f"[ERROR] Erro ao criar ou ajustar tabelas: {e}")

def sincronizar_dados(api_url, tabela, db_path):
    """Sincroniza os dados da API com a tabela do banco de dados."""
    try:
        # Obter os dados da API
        # print(f"[INFO] Sincronizando dados da API: {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        dados = response.json()

        # Verifica se os dados estão na chave 'data'
        if isinstance(dados, dict) and "data" in dados:
            dados = dados["data"]

        if not isinstance(dados, list):
            raise ValueError(f"Os dados da API {api_url} não estão no formato esperado.")

        # print(f"[INFO] Recebidos {len(dados)} registros para a tabela '{tabela}'.")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            if tabela == "estados":
                cursor.execute("DELETE FROM estados")
                for estado in dados:
                    estado_id = int(estado.get("id"))
                    estado_nome = estado.get("name")
                    if estado_id and estado_nome:
                        cursor.execute("INSERT INTO estados (id, nome) VALUES (?, ?)", (estado_id, estado_nome))

            elif tabela == "cidades":
                cursor.execute("DELETE FROM cidades")
                for cidade in dados:
                    cidade_id = int(cidade.get("id"))
                    cidade_nome = cidade.get("name")
                    if cidade_id and cidade_nome:
                        cursor.execute(
                            "INSERT INTO cidades (id, codigo_igbe, nome) VALUES (?, ?, ?)",
                            (cidade_id, cidade_id, cidade_nome),
                        )

            elif tabela == "entidades":
                cursor.execute("DELETE FROM entidades")
                for entidade in dados:
                    entidade_id = entidade.get("entidade_id")
                    codigo_igbe = entidade.get("id")
                    entidade_nome = entidade.get("name")

                    if codigo_igbe and entidade_nome and entidade_id:
                        cursor.execute(
                            "INSERT INTO entidades (id, codigo_igbe, nome, entidade_id) VALUES (?, ?, ?, ?)",
                            (int(codigo_igbe), codigo_igbe, entidade_nome, int(entidade_id)),
                        )

            conn.commit()

        # print(f"[INFO] Dados da tabela '{tabela}' sincronizados com sucesso.")

    except requests.RequestException as e:
        print(f"[ERROR] Erro ao acessar a API {api_url}: {e}")
    except sqlite3.Error as e:
        print(f"[ERROR] Erro ao atualizar a tabela {tabela}: {e}")
    except ValueError as e:
        print(f"[ERROR] Erro de formatação na resposta da API {api_url}: {e}")

def atualizar_entidades(db_path):
    """Atualiza as tabelas de estados, cidades e entidades."""
    if not os.path.exists(db_path):
        # print(f"[INFO] Banco de dados não encontrado. Criando novo banco: {db_path}")
        open(db_path, 'w').close()  # Cria o arquivo do banco de dados vazio

    criar_tabelas(db_path)

    apis = {
        "estados": "https://api.rh247.com.br/230440023/app/sincronizacao/estados",
        "cidades": "https://api.rh247.com.br/230440023/app/sincronizacao/municipios",
        "entidades": "https://api.rh247.com.br/230440023/app/sincronizacao/entidades",
    }

    for tabela, api_url in apis.items():
        sincronizar_dados(api_url, tabela, db_path)

if __name__ == "__main__":
    DB_PATH = "banco_de_dados.db"
    atualizar_entidades(DB_PATH)
