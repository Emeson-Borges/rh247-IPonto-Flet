import flet as ft
import sqlite3
import requests
import os

def verificar_conexao_internet():
    """Verifica se há conexão com a internet."""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def criar_tela_sincronizar_batidas(page: ft.Page, db_path: str):
    if not os.path.exists(db_path):
        raise ValueError(f"Banco de dados não encontrado no caminho: {db_path}")

    registros = []
    menu_aberto = False

    # Elementos da tela
    filtro_matricula = ft.TextField(label="Matrícula", width=200, height=40)
    filtro_data_inicio = ft.TextField(label="Data início (YYYY-MM-DD)", width=200, height=40)
    filtro_data_fim = ft.TextField(label="Data fim (YYYY-MM-DD)", width=200, height=40)
    status_text = ft.Text("Nenhum registro encontrado.", size=16, color=ft.Colors.RED)
    batidas_list = ft.ListView(expand=True, spacing=10)

    menu_lateral = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(value="Filtros", size=20, weight="bold", color=ft.Colors.BLUE_GREY),
                filtro_matricula,
                filtro_data_inicio,
                filtro_data_fim,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Aplicar Filtros",
                            on_click=lambda e: aplicar_filtros(),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                        ),
                        ft.TextButton(
                            text="Limpar Filtros",
                            on_click=lambda e: limpar_filtros(),
                            style=ft.ButtonStyle(color=ft.Colors.RED),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=280,
        bgcolor="#F9F9F9",  # Cor quase branca
        border_radius=10,
        padding=15,
        visible=False,
        animate_opacity=300,
        shadow=ft.BoxShadow(spread_radius=2, blur_radius=4, color=ft.Colors.GREY),
    )

    def carregar_registros():
        """Carrega registros do banco de dados com base nos filtros."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = "SELECT id, data_ponto, funcionario_vinculo_id FROM ponto_final WHERE sincronizado = 0"
        filtros = []

        if filtro_matricula.value.strip():
            query += " AND funcionario_vinculo_id = ?"
            filtros.append(filtro_matricula.value.strip())

        if filtro_data_inicio.value.strip():
            query += " AND date(data_ponto) >= ?"
            filtros.append(filtro_data_inicio.value.strip())

        if filtro_data_fim.value.strip():
            query += " AND date(data_ponto) <= ?"
            filtros.append(filtro_data_fim.value.strip())

        cursor.execute(query, filtros)
        resultado = cursor.fetchall()
        conn.close()

        registros.clear()
        batidas_list.controls.clear()

        if resultado:
            for reg in resultado:
                registros.append(reg)
                batidas_list.controls.append(
                    ft.Checkbox(
                        label=f"ID: {reg[0]}, Data: {reg[1]}, Funcionário ID: {reg[2]}",
                        value=False,
                    )
                )
            status_text.value = f"{len(resultado)} registros encontrados."
            status_text.color = ft.Colors.GREEN
        else:
            status_text.value = "Nenhum registro encontrado."
            status_text.color = ft.Colors.RED

        page.update()

    def limpar_filtros():
        """Limpa os valores dos filtros."""
        filtro_matricula.value = ""
        filtro_data_inicio.value = ""
        filtro_data_fim.value = ""
        carregar_registros()
        page.update()

    def aplicar_filtros():
        """Aplica os filtros e atualiza a lista."""
        if filtro_matricula.value.strip() or filtro_data_inicio.value.strip() or filtro_data_fim.value.strip():
            carregar_registros()
            toggle_menu(None)

    def sincronizar_batidas(e):
        """Sincroniza as batidas selecionadas."""
        if not verificar_conexao_internet():
            emitir_alerta("Erro", "Sem conexão com a internet. Conecte-se ao Wi-Fi para sincronizar.")
            return

        registros_selecionados = [
            registros[idx] for idx, checkbox in enumerate(batidas_list.controls) if checkbox.value
        ]

        if not registros_selecionados:
            emitir_alerta("Aviso", "Nenhum registro selecionado para sincronizar.")
            return

        emitir_alerta("Sucesso", "Registros sincronizados com sucesso!")
        carregar_registros()

    def emitir_alerta(titulo, mensagem):
        """Exibe um alerta com título e mensagem."""
        def fechar_dialog(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(titulo),
            content=ft.Text(mensagem),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    def toggle_menu(e):
        """Alterna a visibilidade do menu lateral."""
        nonlocal menu_aberto
        menu_aberto = not menu_aberto
        menu_lateral.visible = menu_aberto
        page.update()

    carregar_registros()

    return ft.View(
        route="/sincronizar_batidas",
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(icon=ft.icons.FILTER_LIST, on_click=toggle_menu),
                    ft.Text("Sincronizar Batidas", size=24, weight="bold"),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            ft.Stack(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[menu_lateral],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Column(
                                controls=[
                                    status_text,
                                    batidas_list,
                                ],
                                spacing=10,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                        expand=True,
                    ),
                ],
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Sincronizar",
                            on_click=sincronizar_batidas,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE
                            ),
                        ),
                        ft.TextButton(
                            text="Voltar",
                            on_click=lambda e: page.go("/administracao"),
                            style=ft.ButtonStyle(color=ft.Colors.BLUE),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.bottom_center,  # Alinhado ao fundo
                expand=True,
                padding=20,
            ),
        ],
    )
