import os
import sqlite3
import requests
import flet as ft
import base64

DB_PATH = "banco_de_dados.db"
DEFAULT_IMAGE_PATH = "assets/default_image.jpg"

# Função para carregar uma imagem padrão em binário
def carregar_imagem_padrao():
    if os.path.exists(DEFAULT_IMAGE_PATH):
        with open(DEFAULT_IMAGE_PATH, "rb") as f:
            return f.read()
    else:
        return None

DEFAULT_IMAGE_BLOB = carregar_imagem_padrao()

# Função para verificar conexão com a internet
def verificar_conexao_internet():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

# Verificar se funcionário já existe na base local
def funcionario_existe(cursor, funcionario_id):
    cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE funcionario_id = ?", (funcionario_id,))
    return cursor.fetchone()[0] > 0

# Sincronizar dados com a API
def sincronizar_dados_funcionarios(api_url, db_path, tabela, lista_funcionarios, entidade_id, matriculas_map):
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        dados = response.json()["data"]

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            if tabela == "funcionarios":
                for funcionario in dados:
                    funcionario_id = funcionario.get("id", 0)

                    # Ignorar funcionário se já existir
                    if funcionario_existe(cursor, funcionario_id):
                        print(f"Funcionário {funcionario_id} já existe. Ignorado.")
                        continue

                    nome = funcionario.get("nome", "Desconhecido")
                    cpf = funcionario.get("numero_cpf", "00000000000")
                    foto_base64 = funcionario.get("foto_base64", "")
                    matricula = matriculas_map.get(funcionario_id, "0000")

                    try:
                        # Tentar converter a imagem base64 ou usar a imagem padrão
                        try:
                            foto_blob = base64.b64decode(foto_base64)
                        except (base64.binascii.Error, TypeError):
                            foto_blob = DEFAULT_IMAGE_BLOB

                        # Inserir no banco de dados
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO funcionarios (funcionario_id, nome, matricula, entidade_id, cpf, embedding, foto_base64, foto_blob)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                funcionario_id,
                                nome,
                                matricula,
                                entidade_id,
                                cpf,
                                "",
                                foto_base64,
                                foto_blob,
                            ),
                        )
                        lista_funcionarios.append(
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(f"Nome: {nome}", weight="bold", size=16),
                                        ft.Text(f"Matrícula: {matricula} | CPF: {cpf}", size=14),
                                    ],
                                    spacing=5,
                                ),
                                padding=10,
                                border=ft.border.all(1, ft.colors.GREY),
                                border_radius=5,
                                margin=ft.margin.symmetric(horizontal=5, vertical=5),
                            )
                        )
                    except sqlite3.Error as e:
                        print(f"Erro ao salvar funcionário {nome}: {e}")

            elif tabela == "funcionarios_vinculos":
                for vinculo in dados:
                    funcionario_id = vinculo.get("funcionario_id", 0)
                    matricula = vinculo.get("matricula", "0000")
                    matriculas_map[funcionario_id] = matricula

                    try:
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO funcionarios_vinculos (id, matricula, status, funcionario_id)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                vinculo.get("id", 0),
                                matricula,
                                vinculo.get("status", "Desconhecido"),
                                funcionario_id,
                            ),
                        )
                    except sqlite3.Error as e:
                        print(f"Erro ao salvar vínculo {vinculo.get('id', 0)}: {e}")

            conn.commit()

    except requests.RequestException as e:
        print(f"Erro ao acessar API: {e}")

# Criar a tela
def criar_tela_sincronizar_funcionarios(page: ft.Page, db_path: str):
    if not os.path.exists(db_path):
        raise ValueError(f"Banco de dados não encontrado no caminho: {db_path}")

    status_text = ft.Text("Nenhuma ação realizada.", size=16, color=ft.Colors.RED)
    lista_funcionarios = ft.ListView(expand=True, spacing=10)
    loading_spinner = ft.ProgressRing(visible=False, width=50, height=50)
    pesquisa_filtro = ft.Dropdown(
        options=[
            ft.dropdown.Option("nome", "Nome"),
            ft.dropdown.Option("cpf", "CPF"),
            ft.dropdown.Option("matricula", "Matrícula"),
        ],
        value="nome",
        width=120,
    )
    pesquisa_input = ft.TextField(
        label="Pesquisar",
        width=200,
        on_change=lambda e: realizar_pesquisa(pesquisa_filtro.value, e.control.value),
        hint_text="Digite para buscar...",
    )


    def realizar_pesquisa(filtro, valor):
        """
        Função para realizar a pesquisa em tempo real.
        - Para CPF e matrícula, retorna apenas registros exatos.
        - Para Nome, realiza uma busca parcial.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Determina a consulta com base no filtro
            if filtro in ["cpf", "matricula"]:
                query = f"SELECT DISTINCT nome, matricula, cpf FROM funcionarios WHERE {filtro} = ?"
                cursor.execute(query, (valor.strip(),))  # Busca exata para CPF e matrícula
            else:  # Busca por nome (parcial)
                query = f"SELECT DISTINCT nome, matricula, cpf FROM funcionarios WHERE {filtro} LIKE ?"
                cursor.execute(query, (f"%{valor.strip()}%",))  # Busca parcial para nome

            resultados = cursor.fetchall()

            # Atualiza a lista de funcionários
            lista_funcionarios.controls.clear()

            if resultados:
                for nome, matricula, cpf in resultados:
                    lista_funcionarios.controls.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(f"Nome: {nome}", weight="bold", size=16),
                                    ft.Text(f"Matrícula: {matricula} | CPF: {cpf}", size=14),
                                ],
                                spacing=5,
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.colors.GREY),
                            border_radius=5,
                            margin=ft.margin.symmetric(horizontal=5, vertical=5),
                        )
                    )
            else:
                # Exibe mensagem informando que nenhum registro foi encontrado
                lista_funcionarios.controls.append(
                    ft.Text("Nenhum registro encontrado.", size=16, color=ft.colors.RED)
                )

        # Atualiza a interface para refletir as mudanças
        page.update()


    def importar_da_web(e):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entidade_id FROM entidades_configuradas LIMIT 1")
            result = cursor.fetchone()
            if result:
                entidade_id = result[0]
            else:
                status_text.value = "Entidade não configurada."
                status_text.color = ft.Colors.RED
                page.update()
                return

        if not verificar_conexao_internet():
            status_text.value = "Sem conexão com a internet."
            status_text.color = ft.Colors.RED
            page.update()
            return

        funcionarios_url = f"https://api.rh247.com.br/230440023/app/sincronizacao/funcionarios?entidade_id={entidade_id}"
        vinculos_url = f"https://api.rh247.com.br/230440023/app/sincronizacao/funcionarios-vinculos?entidade_id={entidade_id}"

        matriculas_map = {}
        loading_spinner.visible = True
        lista_funcionarios.controls.clear()
        page.update()

        sincronizar_dados_funcionarios(vinculos_url, db_path, "funcionarios_vinculos", lista_funcionarios.controls, entidade_id, matriculas_map)
        sincronizar_dados_funcionarios(funcionarios_url, db_path, "funcionarios", lista_funcionarios.controls, entidade_id, matriculas_map)

        loading_spinner.visible = False
        if lista_funcionarios.controls:
            status_text.value = "Funcionários e vínculos importados com sucesso."
            status_text.color = ft.Colors.GREEN
        else:
            status_text.value = "Nenhum dado importado. Verifique os logs."
            status_text.color = ft.Colors.RED
        page.update()

    def sincronizar_local(e):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM funcionarios")
            funcionarios = cursor.fetchall()

            if not funcionarios:
                status_text.value = "Nenhum funcionário para sincronizar."
                status_text.color = ft.Colors.RED
                page.update()
                return

            payload = [{"id": func[0], "nome": func[1], "matricula": func[2]} for func in funcionarios]

            try:
                response = requests.post(
                    "https://api.rh247.com.br/230440023/app/sincronizacao/salvar-funcionarios",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                status_text.value = "Funcionários sincronizados com sucesso!"
                status_text.color = ft.Colors.GREEN
            except requests.RequestException as e:
                status_text.value = f"Erro ao sincronizar: {e}"
                status_text.color = ft.Colors.RED
        page.update()

    def cancelar(e):
        page.go("/administracao")

    return ft.View(
        route="/sincronizar_funcionarios",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Sincronizar Funcionários", size=24, weight="bold"),
                    ft.Row(
                        controls=[pesquisa_filtro, pesquisa_input],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    loading_spinner,
                    lista_funcionarios,
                    status_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Importar da Web",
                            on_click=importar_da_web,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            text="Sincronizar Local",
                            on_click=sincronizar_local,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    spacing=20,
                ),
                alignment=ft.alignment.bottom_center,
                padding=20,
            ),
            ft.Container(
                content=ft.TextButton(
                    text="Cancelar",
                    on_click=cancelar,
                    style=ft.ButtonStyle(
                        color=ft.Colors.BLUE,
                        padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                    ),
                ),
                alignment=ft.alignment.center,
                padding=20,
            ),
        ],
    )
