import flet as ft
import base64
import hashlib
from threading import Thread
import sqlite3
import os
import time
import cv2

def criar_tela_prova_vida(page: ft.Page, db_path: str):
    """
    Tela para cadastro facial no banco de dados.
    """
    if not os.path.exists(db_path):
        raise ValueError(f"Banco de dados não encontrado no caminho: {db_path}")

    # Componentes visuais
    status_text = ft.Text("Inicializando câmera...", size=20, weight="bold", color=ft.Colors.BLUE)
    camera_feed = ft.Image(width=300, height=300)
    nome_input = ft.TextField(label="Nome do Funcionário", width=300)
    matricula_input = ft.TextField(label="Matrícula do Funcionário", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    stop_camera = False
    rosto_capturado = None

    def update_images():
        """Captura frames da câmera e detecta rostos usando OpenCV."""
        nonlocal stop_camera, rosto_capturado

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            status_text.value = "Erro: Não foi possível acessar a câmera."
            status_text.color = ft.Colors.RED
            page.update()
            return

        status_text.value = "Câmera iniciada. Posicione seu rosto."
        status_text.color = ft.Colors.GREEN
        page.update()

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while not stop_camera:
            ret, frame = cap.read()
            if ret:
                # Converter frame para escala de cinza
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Detectar rostos
                faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                for (x, y, w, h) in faces:
                    # Capturar o rosto detectado
                    rosto_capturado = gray_frame[y:y + h, x:x + w]

                    # Desenhar a caixa no rosto
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Converter para base64 para exibição no Flet
                _, buffer = cv2.imencode(".jpg", frame)
                frame_base64 = base64.b64encode(buffer).decode("utf-8")
                camera_feed.src_base64 = frame_base64
                page.update()

            time.sleep(0.03)

        cap.release()

    def cadastrar_facial():
        """Cadastra o funcionário no banco de dados."""
        if not nome_input.value or not matricula_input.value:
            emitir_alerta("Erro", "Por favor, preencha todos os campos.")
            return

        if rosto_capturado is None:
            emitir_alerta("Erro", "Nenhum rosto foi detectado. Aguarde a detecção.")
            return

        # Gerar hash_encoding único
        try:
            rosto_hash = hashlib.sha256(rosto_capturado.tobytes()).hexdigest()

            # Inserir no banco de dados
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO dados_faciais (nome, matricula, hash_encoding)
                VALUES (?, ?, ?)
            """, (nome_input.value, matricula_input.value, rosto_hash))

            conn.commit()
            conn.close()

            emitir_alerta("Sucesso", "Cadastro realizado com sucesso!")
            limpar_campos()
        except sqlite3.IntegrityError:
            emitir_alerta("Erro", "A matrícula ou facial já estão cadastradas.")
        except Exception as e:
            emitir_alerta("Erro", f"Ocorreu um erro: {e}")

    def emitir_alerta(titulo, mensagem):
        """Exibe um alerta para o usuário."""
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

    def limpar_campos():
        """Limpa os campos de entrada."""
        nome_input.value = ""
        matricula_input.value = ""
        page.update()

    def start_camera():
        """Inicia a câmera automaticamente."""
        nonlocal stop_camera
        stop_camera = False
        Thread(target=update_images, daemon=True).start()

    def stop_camera_feed(e):
        """Interrompe a câmera ao clicar em voltar."""
        nonlocal stop_camera
        stop_camera = True
        status_text.value = "Câmera pausada."
        status_text.color = ft.Colors.BLUE
        page.update()
        page.go("/")

    # Inicia a câmera automaticamente
    start_camera()

    # Retorna a tela com layout ajustado
    return ft.View(
        route="/prova_vida",
        controls=[
            ft.Column(
                controls=[
                    camera_feed,
                    status_text,
                    nome_input,
                    matricula_input,
                    ft.ElevatedButton(
                        text="Cadastrar Facial",
                        on_click=lambda e: cadastrar_facial(),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.Padding(20, 10, 20, 10),
                        ),
                    ),
                    ft.ElevatedButton(
                        text="Voltar",
                        on_click=stop_camera_feed,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.Padding(20, 10, 20, 10),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
    )
