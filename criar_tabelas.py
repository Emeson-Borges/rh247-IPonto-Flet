import sqlite3

# Define as SQLs para criação das tabelas
SQLS = {
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
    
    "CREATE_TABLE_ENTIDADE_CONFIGURADA": """
        CREATE TABLE IF NOT EXISTS entidades_configuradas (
            id INTEGER PRIMARY KEY NOT NULL,
            entidade_id INTEGER NOT NULL,
            estado_nome VARCHAR(200) NOT NULL,
            cidade_nome VARCHAR(200) NOT NULL,
            codigo_igbe VARCHAR(200) NOT NULL,
            name VARCHAR(200) NOT NULL
        );
    """,
    

    "CREATE_TABLE_FUNCIONARIOS": """
        CREATE TABLE IF NOT EXISTS funcionarios (
            funcionario_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(200) NOT NULL,
            matricula VARCHAR(100) NOT NULL, 
            entidade_id INTEGER NOT NULL,
            cpf VARCHAR(14) NOT NULL,
            embedding TEXT NOT NULL,
            foto_base64 TEXT NOT NULL,
            foto_blob BLOB NOT NULL
        );
    """,

    "CREATE_TABLE_FUNCIONARIOS_VINCULOS": """
        CREATE TABLE IF NOT EXISTS funcionarios_vinculos (
            id INTEGER PRIMARY KEY NOT NULL, 
            matricula VARCHAR(100) NOT NULL, 
            status INTEGER NOT NULL DEFAULT 1, 
            funcionario_id INTEGER NOT NULL
        );
    """,

    "CREATE_TABLE_PONTO_FINAL": """
        CREATE TABLE IF NOT EXISTS ponto_final (
            id INTEGER PRIMARY KEY NOT NULL, 
            data_ponto DATETIME NOT NULL, 
            funcionario_vinculo_id INTEGER NOT NULL,
            sincronizado INTEGER NOT NULL DEFAULT 0 
        );
    """,
}

def criar_tabelas(db_path):
    """Verifica e cria as tabelas no banco de dados, se não existirem."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for table_name, create_table_sql in SQLS.items():
            # print(f"Verificando/criando tabela: {table_name}...")
            cursor.execute(create_table_sql)

        conn.commit()
        # print("Tabelas verificadas/criadas com sucesso!")

    # except sqlite3.Error as e:
        # print(f"Erro ao criar tabelas: {e}")

    finally:
        if conn:
            conn.close()

# Exemplo de uso
if __name__ == "__main__":
    db_path = "banco_de_dados.db"  # Substitua pelo caminho do seu banco de dados
    criar_tabelas(db_path)
