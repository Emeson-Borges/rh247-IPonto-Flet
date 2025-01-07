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
    selecionados = set()
    selecionar_varios = True

    # Contador de itens selecionados
    contador_selecionados = ft.Text("0 itens selecionados", size=16, color=ft.Colors.BLUE)

    # Elementos da lista de registros
    batidas_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)

    def carregar_registros():
        """Carrega registros do banco de dados."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.id, p.data_ponto, f.nome, f.matricula
            FROM ponto_final p
            LEFT JOIN funcionarios f ON p.funcionario_vinculo_id = f.funcionario_id
            WHERE p.sincronizado = 0
            """
        )
        resultado = cursor.fetchall()
        conn.close()

        registros.clear()
        batidas_list.controls.clear()
        selecionados.clear()

        if resultado:
            for reg in resultado:
                registros.append(reg)
                registro_id, data_hora, nome, matricula = reg

                # Criação da linha formatada
                batidas_list.controls.append(
                    ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=False,
                                on_change=lambda e, reg_id=registro_id: alternar_selecao(reg_id, e.control.value),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{nome if nome else 'Funcionário Desconhecido'}", size=16, weight="bold"),
                                    ft.Text(f"Matrícula: {matricula if matricula else 'N/A'}"),
                                    ft.Text(f"Data e Hora: {data_hora}"),
                                ],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
            contador_selecionados.value = "0 itens selecionados"
        else:
            batidas_list.controls.append(ft.Text("Nenhum registro encontrado.", size=16, color=ft.Colors.RED))

        page.update()

    def alternar_selecao(registro_id, selecionado):
        """Alterna a seleção de um registro."""
        if selecionado:
            selecionados.add(registro_id)
        else:
            selecionados.discard(registro_id)

        contador_selecionados.value = f"{len(selecionados)} itens selecionados"
        page.update()

    def selecionar_varios_ou_desmarcar():
        """Seleciona ou desmarca até 50 registros."""
        nonlocal selecionar_varios

        if selecionar_varios:
            # Seleciona até 50 registros
            for idx, reg in enumerate(registros):
                if idx >= 50:
                    break
                selecionados.add(reg[0])

        else:
            # Desmarca todos
            selecionados.clear()

        # Atualiza os checkboxes e o estado do botão
        for checkbox, reg in zip(batidas_list.controls, registros):
            checkbox.controls[0].value = reg[0] in selecionados

        selecionar_varios = not selecionar_varios
        selecionar_btn.text = "Desmarcar" if not selecionar_varios else "Selecionar Vários"
        contador_selecionados.value = f"{len(selecionados)} itens selecionados"
        page.update()

    def sincronizar_batidas():
        """Sincroniza as batidas selecionadas."""
        if not verificar_conexao_internet():
            emitir_alerta("Erro", "Sem conexão com a internet. Conecte-se ao Wi-Fi para sincronizar.")
            return

        if not selecionados:
            emitir_alerta("Aviso", "Nenhum registro selecionado para sincronizar.")
            return

        # Simulação de sincronização
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for registro_id in selecionados:
            cursor.execute("UPDATE ponto_final SET sincronizado = 1 WHERE id = ?", (registro_id,))

        conn.commit()
        conn.close()

        emitir_alerta("Sucesso", "Registros sincronizados com sucesso!")
        carregar_registros()

    def emitir_alerta(titulo, mensagem):
        """Exibe um alerta com título e mensagem."""
        def fechar_dialog(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(titulo, size=18, weight="bold"),
            content=ft.Text(mensagem, size=14),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    carregar_registros()

    selecionar_btn = ft.ElevatedButton(
        text="Selecionar Vários",
        on_click=lambda _: selecionar_varios_ou_desmarcar(),
        bgcolor=ft.Colors.BLUE,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE  # Define a cor no estilo do botão
        ),
    )

    sincronizar_btn = ft.ElevatedButton(
        text="Sincronizar",
        on_click=lambda _: sincronizar_batidas(),
        bgcolor=ft.Colors.GREEN,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE  # Define a cor no estilo do botão
        ),
    )

    voltar_btn = ft.TextButton(
        text="Voltar",
        on_click=lambda _: page.go("/administracao"),
        style=ft.ButtonStyle(
            color=ft.Colors.BLUE  # Define a cor no estilo do botão
        ),
    )

    # Layout principal
    return ft.View(
        route="/sincronizar_batidas",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Sincronizar Batidas", size=24, weight="bold"),
                    contador_selecionados,
                    batidas_list,
                ],
                expand=True,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[selecionar_btn, sincronizar_btn, voltar_btn],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                bgcolor=ft.Colors.WHITE,
                padding=10,
            ),
        ],
    )
