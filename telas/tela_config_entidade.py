import sqlite3
import flet as ft
import os

def criar_tabela_configuracao(db_path):
    """Cria a tabela de entidades configuradas se não existir."""
    tabela = """
        CREATE TABLE IF NOT EXISTS entidades_configuradas (
            id INTEGER PRIMARY KEY NOT NULL,
            entidade_id INTEGER NOT NULL,
            estado_nome VARCHAR(200) NOT NULL,
            cidade_nome VARCHAR(200) NOT NULL,
            codigo_igbe VARCHAR(200) NOT NULL,
            name VARCHAR(200) NOT NULL
        );
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(tabela)
    conn.commit()
    conn.close()

def carregar_opcoes(db_path, tabela):
    """Carrega as opções de estado, cidade ou entidade do banco de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, nome FROM {tabela}")
    opcoes = cursor.fetchall()
    conn.close()
    return opcoes

def carregar_entidades(db_path):
    """Carrega todas as entidades disponíveis no banco de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = """
        SELECT id, entidade_id, nome FROM entidades
    """
    cursor.execute(query)
    entidades = cursor.fetchall()
    conn.close()
    return entidades

def salvar_configuracao(db_path, entidade_id, estado_nome, cidade_nome, codigo_igbe, entidade_nome):
    """Salva a configuração selecionada na tabela de entidades configuradas."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entidades_configuradas")  # Remove a configuração anterior

    # Insere a nova configuração
    cursor.execute(
        """
        INSERT INTO entidades_configuradas (entidade_id, estado_nome, cidade_nome, codigo_igbe, name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            entidade_id,  # Salva o entidade_id da tabela entidades
            estado_nome,
            cidade_nome,
            codigo_igbe,
            entidade_nome,  # Nome da entidade
        ),
    )
    conn.commit()
    conn.close()

def criar_tela_config_entidade(page: ft.Page, db_path: str):
    if not os.path.exists(db_path):
        raise ValueError(f"Banco de dados não encontrado no caminho: {db_path}")

    criar_tabela_configuracao(db_path)

    estados = carregar_opcoes(db_path, "estados")
    cidades = []
    entidades = []

    estado_dropdown = ft.Dropdown(
        label="Selecione o Estado",
        options=[],
        on_change=lambda e: carregar_cidades(),
        border_radius=10,
        filled=True,
        width=300
    )
    cidade_dropdown = ft.Dropdown(
        label="Selecione o Município",
        options=[],
        on_change=lambda e: carregar_entidades_opcoes(),
        border_radius=10,
        filled=True,
        width=300
    )
    entidade_dropdown = ft.Dropdown(
        label="Selecione a Entidade",
        options=[],
        border_radius=10,
        filled=True,
        width=300
    )

    status_text = ft.Text("", color=ft.Colors.RED, size=16)

    def carregar_estados():
        """Carrega os estados no dropdown."""
        estado_dropdown.options = [ft.dropdown.Option(str(estado[0]), estado[1]) for estado in estados]
        page.update()

    def carregar_cidades():
        """Carrega os municípios no dropdown com base no estado selecionado."""
        nonlocal cidades
        estado_id = estado_dropdown.value
        if not estado_id:
            return
        cidades = carregar_opcoes(db_path, "cidades")
        cidade_dropdown.options = [
            ft.dropdown.Option(str(cidade[0]), cidade[1]) for cidade in cidades
        ]
        page.update()

    def carregar_entidades_opcoes():
        """Carrega todas as entidades disponíveis."""
        nonlocal entidades
        entidades = carregar_entidades(db_path)
        entidade_dropdown.options = [
            ft.dropdown.Option(str(entidade[1]), entidade[2]) for entidade in entidades
        ]
        page.update()

    def salvar_configuracao_app(e):
        """Salva a configuração selecionada no banco de dados."""
        estado_id = estado_dropdown.value
        cidade_id = cidade_dropdown.value
        entidade_id = entidade_dropdown.value

        if not (estado_id and cidade_id and entidade_id):
            status_text.value = "Por favor, selecione todas as opções antes de salvar."
            page.update()
            return

        # Obter os nomes de estado e cidade
        estado_nome = next((estado[1] for estado in estados if str(estado[0]) == estado_id), "")
        cidade_nome = next((cidade[1] for cidade in cidades if str(cidade[0]) == cidade_id), "")

        # Obter o nome da entidade selecionada
        entidade_nome = next((entidade[2] for entidade in entidades if str(entidade[1]) == entidade_id), "")

        if not (estado_nome and cidade_nome and entidade_nome):
            status_text.value = "Erro ao salvar: informações incompletas."
            page.update()
            return

        # Gerar código IBGE
        codigo_igbe = f"{cidade_id}-{estado_id}"

        salvar_configuracao(db_path, int(entidade_id), estado_nome, cidade_nome, codigo_igbe, entidade_nome)

        # Exibe sucesso e redireciona
        status_text.value = "Configuração salva com sucesso!"
        status_text.color = ft.Colors.GREEN
        page.update()
        page.go("/administracao")

    def voltar(e):
        """Voltar para a tela de administração."""
        page.go("/administracao")

    carregar_estados()

    return ft.View(
        route="/config_entidade",
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Image(src="../assets/rh247_azul.png", width=120),
                                ft.Text(
                                    "Configuração de Entidade",
                                    size=20,
                                    weight="bold",
                                    text_align="center",
                                    color=ft.Colors.BLUE
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        padding=20
                    ),
                    estado_dropdown,
                    cidade_dropdown,
                    entidade_dropdown,
                    ft.ElevatedButton(
                        text="Salvar Configuração",
                        on_click=salvar_configuracao_app,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                        width=300,
                    ),
                    status_text,
                    ft.TextButton(
                        text="Voltar",
                        on_click=voltar,
                        style=ft.ButtonStyle(
                            color=ft.Colors.BLUE,
                            padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
        ],
    )
