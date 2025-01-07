import flet as ft
import sqlite3
import datetime

def criar_tela_administracao(page, db_connection):
    db_connection = sqlite3.connect("banco_de_dados.db")
    # Função para voltar à tela principal
    def voltar(e):
        page.go("/")

    # Função para criar os cards com navegação
    def criar_card(icone, texto, subtitulo, rota):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(name=icone, size=30, color=ft.colors.BLUE),
                    ft.Text(value=texto, size=14, weight="bold", text_align="center"),
                    ft.Text(value=subtitulo, size=12, color="#666666", text_align="center"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            width=140,
            height=140,
            border_radius=15,
            alignment=ft.alignment.center,
            bgcolor=ft.colors.WHITE,
            padding=10,
            on_click=lambda e: page.go(rota),
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=2,
                color="#000",  # Cinza com 20% de opacidade
            ),
        )

    # Recuperar entidade configurada
    def obter_entidade_configurada():
        cursor = db_connection.cursor()
        cursor.execute("SELECT estado_nome, cidade_nome, name, codigo_igbe FROM entidades_configuradas LIMIT 1")
        entidade = cursor.fetchone()
        if entidade:
            return entidade[0], entidade[1], entidade[2], entidade[3]
        return "", "", "", ""

    entidade_nome, cidade_nome, estado_nome, codigo_igbe = obter_entidade_configurada()
    db_connection.close()  # Feche a conexão ao final do uso
    # Obter o mês atual
    mes_atual = datetime.datetime.now().strftime("%b/%Y").upper()

    # Layout da tela de administração com scroll
    layout = ft.Column(
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        scroll="adaptive",  # Adiciona scroll adaptativo
        controls=[
            # Cabeçalho com informações da entidade
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Text("E", size=24, weight="bold"),
                            bgcolor=ft.colors.BLUE,
                            radius=30,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    value=f"Entidade Configurada", size=14, weight="bold", color="#666666"
                                ),
                                ft.Text(
                                    value=entidade_nome or "Entidade não configurada",
                                    size=16,
                                    weight="bold",
                                    color="#333333",
                                ),
                                ft.Text(
                                    value=f"Código IBGE: {codigo_igbe}" if codigo_igbe else "",
                                    size=14,
                                    color="#666666",
                                ),
                                ft.TextButton(
                                    text="Alterar Configuração",
                                    on_click=lambda e: page.go("/config_entidade"),
                                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                                ),
                            ],
                        ),
                    ],
                    spacing=15,
                ),
                padding=20,
                bgcolor="#F5F5F5",
                border_radius=10,
            ),

            # Card de competência
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value="Competência", size=14, color=ft.colors.WHITE),
                        ft.Text(value=mes_atual, size=18, weight="bold", color=ft.colors.WHITE),
                        ft.Icon(name="calendar_today", color=ft.colors.WHITE, size=20),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=20,
                bgcolor=ft.colors.BLUE,
                border_radius=10,
            ),

            # Grid de cards
            ft.GridView(
                expand=False,
                runs_count=2,
                spacing=15,
                max_extent=160,
                controls=[
                    criar_card("autorenew", "Sincronizar", "Sincronizar pontos", "/sincronizar"),
                    criar_card("schedule", "Frequência Diária", "Veja seu espelho de ponto", "/frequencia"),
                    criar_card("event_note", "Lembretes", "Acesse seus lembretes", "/lembretes"),
                    criar_card("settings", "Entidade", "Configurar entidade", "/config_entidade"),
                    criar_card("supervised_user_circle", "Funcionários", "Cadastrar funcionários", "/cadastrar_funcionario"),
                    criar_card("face", "Ponto Facial", "Acesse o ponto facial", "/registro_ponto"),
                ],
            ),

            # Botão de voltar como um link azul
            ft.TextButton(
                text="Voltar",
                on_click=voltar,
                style=ft.ButtonStyle(
                    color=ft.colors.BLUE,
                    padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                ),
            ),
        ],
    )

    # Retorna a tela como um View com scroll
    return ft.View(
        route="/administracao",
        scroll="adaptive",  # Adiciona scroll ao nível da view inteira
        controls=[layout],
    )
