import flet as ft
import sqlite3
import datetime
import asyncio
import locale
from telas.tela_administracao import criar_tela_administracao  # Importa a tela de administração
from telas.tela_registro_ponto import criar_tela_registro_ponto  # Importa a tela de registro de ponto
from telas.tela_prova_vida import criar_tela_prova_vida
from telas.tela_cadastrar_funcionario import criar_tela_cadastrar_funcionario
from telas.tela_sincronizar_batidas import criar_tela_sincronizar_batidas
from updates_entidades import atualizar_entidades
from telas.tela_config_entidade import criar_tela_config_entidade
from telas.tela_sincronizar_funcionarios import criar_tela_sincronizar_funcionarios




from criar_tabelas import criar_tabelas

DB_PATH = "banco_de_dados.db"
db_connection = sqlite3.connect("banco_de_dados.db", check_same_thread=False)



# db_connection = sqlite3.connect("banco_de_dados.db")

# Configurar o locale para português
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

def criar_tela_login(page):
    # Função para validar o PIN
    def verificar_pin():
        
        senha = "".join([campo.value for campo in senha_inputs])
        if senha == "123456":  # PIN correto (exemplo: 123456)
            page.go("/administracao")
        else:
            exibir_erro("PIN incorreto. Tente novamente.")
            for campo in senha_inputs:  # Limpa todos os campos
                campo.value = ""
            senha_inputs[0].focus()  # Volta o foco para o primeiro campo
            page.update()

    # Função para exibir mensagem de erro
    def exibir_erro(mensagem):
        def fechar_dialog(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Erro"),
            content=ft.Text(mensagem),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    # Função para mover o foco automaticamente
    def mover_foco(instance):
        if len(instance.value) == 1:  # Quando o campo tiver 1 dígito
            index = senha_inputs.index(instance)
            if index < len(senha_inputs) - 1:  # Se não for o último campo
                senha_inputs[index + 1].focus()
            elif index == len(senha_inputs) - 1:  # Se for o último campo
                verificar_pin()  # Verifica a senha automaticamente

    # Layout para a tela de login
    senha_inputs = []
    for _ in range(6):
        campo_senha = ft.TextField(
            password=True,
            width=20,
            height=20,
            border_radius=25,  # Campos redondos
            text_align="center",
            max_length=1,  # Apenas 1 número por campo
            keyboard_type=ft.KeyboardType.NUMBER,  # Apenas números
            on_change=lambda e: mover_foco(e.control),  # Chama mover_foco ao alterar o valor
        )
        senha_inputs.append(campo_senha)

    layout = ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Text(
                value="Insira o PIN de acesso",
                size=18,
                weight="bold",
                text_align="center",
            ),
            ft.Row(
                controls=senha_inputs,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,  # Espaço entre os campos
            ),
            ft.TextButton(
                text="Voltar",
                on_click=lambda e: page.go("/"),
                style=ft.ButtonStyle(color=ft.colors.BLUE),
            ),
        ],
    )

    # Retorna a tela como um View centralizada
    return ft.View(
        route="/login",
        controls=[
            ft.Container(
                content=layout,
                alignment=ft.alignment.center,
                expand=True,  # Faz com que todo o conteúdo seja centralizado na tela
            )
        ],
    )
    
# Conexão única com o banco
conn = sqlite3.connect("banco_dados.db")

def main(page: ft.Page):
    # Chamar a função para criar ou atualizar as tabelas no banco de dados
    criar_tabelas(DB_PATH)
    atualizar_entidades(DB_PATH)
    
    
    # Configurações da página
    page.title = "RH247"
    page.window_width = 360
    page.window_height = 640
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Elementos da interface
    saudacao = ft.Text(value="Carregando...", size=22, weight="bold", text_align="center", color=ft.colors.BLACK)
    horario = ft.Text(value="00:00:00", size=36, weight="bold", text_align="center", color="#1A82C3")
    data = ft.Text(value="Carregando data...", size=18, text_align="center", color="#666666")

    # Função para atualizar a saudação, hora e data
    def atualizar_tempo():
        agora = datetime.datetime.now()
        saudacao.value = "Bom dia" if agora.hour < 12 else "Boa tarde" if agora.hour < 18 else "Boa noite"
        horario.value = agora.strftime("%H:%M:%S")
        data.value = agora.strftime("%d de %B de %Y")
        page.update()

    # Navegar para as telas
    def navegar(rota):
        if rota == "/":
            page.views.clear()
            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=20,
                                controls=[
                                    ft.Image(
                                        src="../assets/rh247_azul.png",
                                        width=150,
                                        height=150,
                                        fit=ft.ImageFit.CONTAIN,
                                    ),
                                    saudacao,
                                    horario,
                                    data,
                                    ft.ElevatedButton(
                                        text="Registrar Ponto",
                                        on_click=lambda e: page.go("/registro_ponto"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.colors.LIGHT_GREEN,
                                            color=ft.colors.WHITE,
                                            shape=ft.RoundedRectangleBorder(radius=50),
                                            padding=ft.Padding(left=55, top=22, right=55, bottom=25),
                                        ),
                                    ),
                                    ft.ElevatedButton(
                                        text="Administrativo",
                                        on_click=lambda e: page.go("/login"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.colors.LIGHT_BLUE,
                                            color=ft.colors.WHITE,
                                            shape=ft.RoundedRectangleBorder(radius=50),
                                            padding=ft.Padding(left=55, top=22, right=55, bottom=25),
                                        ),
                                    ),
                                ],
                            ),
                            alignment=ft.alignment.center,
                            expand=True,
                        )
                    ],
                )
            )
        elif rota == "/config_entidade":
            page.views.append(criar_tela_config_entidade(page, db_path="banco_de_dados.db"))
        elif rota == "/sincronizar_funcionarios":
            page.views.append(criar_tela_sincronizar_funcionarios(page, DB_PATH))
        elif rota == "/sincronizar":
            page.views.append(criar_tela_sincronizar_batidas(page, DB_PATH))
        elif rota == "/cadastrar_funcionario":
            page.views.append(criar_tela_cadastrar_funcionario(page))
        elif rota == "/login":
            page.views.append(criar_tela_login(page))
        elif rota == "/administracao":
            page.views.append(criar_tela_administracao(page, db_connection))
        elif rota == "/registro_ponto":
            page.views.append(criar_tela_registro_ponto(page, DB_PATH))  # Vai para a tela de registro de ponto
        elif rota == "/prova_vida":
            page.views.append(criar_tela_prova_vida(page, DB_PATH))  # Passa o caminho do banco de dados
        # Adicione outras rotas aqui
        page.update()

    # Configurar rotas
    page.on_route_change = lambda e: navegar(page.route)
    page.go("/")  # Inicializa na tela principal

    # Atualizar relógio em tempo real
    async def atualizar_relogio():
        while True:
            atualizar_tempo()
            await asyncio.sleep(1)

    asyncio.run(atualizar_relogio())

ft.app(target=main)
