import os
import sqlite3
import cv2
import base64
import time
import re
import json
import numpy as np
from threading import Thread
import flet as ft

DB_PATH = "banco_de_dados.db"

def validar_cpf_formatado(cpf):
    return re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf) is not None

def formatar_cpf(cpf):
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) > 3:
        cpf = cpf[:3] + "." + cpf[3:]
    if len(cpf) > 7:
        cpf = cpf[:7] + "." + cpf[7:]
    if len(cpf) > 11:
        cpf = cpf[:11] + "-" + cpf[11:]
    return cpf[:14]

def criar_tela_cadastrar_funcionario(page):
    # Variáveis de estado
    rosto_capturado = None
    hash_gerado = None  # Será o "embedding" (hash da imagem)

    def capturar_rosto():
        nonlocal rosto_capturado, hash_gerado

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            emitir_alerta("Erro", "Não foi possível acessar a câmera.")
            return

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        start_time = time.time()
        capture_duration = 10  # tempo máximo de captura (segundos)

        while time.time() - start_time < capture_duration:
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))

            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                rosto_capturado = frame[y : y + h, x : x + w]

                # Desenha elipse no rosto
                center = (x + w // 2, y + h // 2)
                axes = (w // 2 + 20, h // 2 + 30)
                cv2.ellipse(frame, center, axes, 0, 0, 360, (0, 255, 0), 2)

            # Mostra frame no Flet
            _, buffer = cv2.imencode(".jpg", frame)
            camera_feed.src_base64 = base64.b64encode(buffer).decode("utf-8")
            page.update()

        cap.release()

        # Se capturamos um rosto, gerar o hash
        if rosto_capturado is not None:
            hash_gerado = gerar_hash_facial(rosto_capturado)
        else:
            hash_gerado = None

        verificar_campos()

    def gerar_hash_facial(bgr_image):
        """
        Gera um hash (pHash) da imagem recortada do rosto.
        Retorna um array de 8 bytes ou algo semelhante.
        Em OpenCV, precisamos instalar `opencv-contrib-python` para usar cv2.img_hash.
        """
        if len(bgr_image.shape) == 3:
            gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = bgr_image

        hasher = cv2.img_hash.PHash_create()  # ou AverageHash_create(), etc.
        hash_val = hasher.compute(gray)  # Retorna um np.array shape (1, 8), dtype=uint8
        # Convertendo em hex para salvar no banco como string
        hash_hex = hash_val.flatten().tobytes().hex()
        return hash_hex

    def verificar_campos():
        # Habilita "Salvar" se todos campos e hash_gerado existirem
        salvar_btn.disabled = not (
            nome_input.value.strip()
            and validar_cpf_formatado(cpf_input.value.strip())
            and matricula_input.value.strip()
            and entidade_input.value.strip()
            and hash_gerado is not None
        )
        page.update()

    def salvar_funcionario():
        if not nome_input.value or not cpf_input.value or not matricula_input.value or not entidade_input.value:
            emitir_alerta("Erro", "Preencha todos os campos.")
            return
        if not hash_gerado:
            emitir_alerta("Erro", "Nenhum rosto foi capturado.")
            return

        # Remove mascara do CPF
        cpf_somente_numeros = re.sub(r"\D", "", cpf_input.value.strip())

        # Salva imagem do rosto, etc.
        try:
            # Salva a foto do rosto
            pasta_prova_vida = "prova_vida"
            if not os.path.exists(pasta_prova_vida):
                os.makedirs(pasta_prova_vida)

            filename = f"{nome_input.value.strip()}_{cpf_somente_numeros}.jpg"
            path_arquivo = os.path.join(pasta_prova_vida, filename)
            cv2.imwrite(path_arquivo, rosto_capturado)

            with open(path_arquivo, "rb") as f:
                foto_bin = f.read()
            foto_base64 = base64.b64encode(foto_bin).decode("utf-8")

            # Salva no banco
            with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO funcionarios (
                        nome, matricula, entidade_id, cpf, embedding, foto_base64, foto_blob
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome_input.value.strip(),
                    int(matricula_input.value.strip()),
                    int(entidade_input.value.strip()),
                    cpf_somente_numeros,
                    hash_gerado,        # Aqui salvamos o "hash" (pHash) como string
                    foto_base64,
                    foto_bin
                ))
                conn.commit()

            emitir_alerta("Sucesso", "Funcionário cadastrado com sucesso!")
            limpar_campos()
        except Exception as e:
            emitir_alerta("Erro", f"Ocorreu um erro: {e}")

    def emitir_alerta(titulo, mensagem):
        def fechar_dialog(_):
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
        nonlocal rosto_capturado, hash_gerado
        nome_input.value = ""
        cpf_input.value = ""
        matricula_input.value = ""
        entidade_input.value = ""
        camera_feed.src_base64 = ""
        salvar_btn.disabled = True
        rosto_capturado = None
        hash_gerado = None
        page.update()

    # -------------- UI --------------
    nome_input = ft.TextField(label="Nome", width=300, on_change=lambda _: verificar_campos())
    cpf_input = ft.TextField(
        label="CPF (000.000.000-00)",
        width=300,
        on_change=lambda _: (
            setattr(cpf_input, "value", formatar_cpf(cpf_input.value)),
            verificar_campos()
        ),
    )
    matricula_input = ft.TextField(
        label="Matrícula",
        width=300,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: verificar_campos()
    )
    entidade_input = ft.TextField(
        label="Entidade ID",
        width=300,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: verificar_campos()
    )
    camera_feed = ft.Image(width=300, height=300)

    capturar_btn = ft.ElevatedButton(
        text="Capturar Rosto",
        on_click=lambda _: Thread(target=capturar_rosto, daemon=True).start(),
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
    )

    salvar_btn = ft.ElevatedButton(
        text="Salvar Funcionário",
        on_click=lambda _: salvar_funcionario(),
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
        disabled=True,
    )

    voltar_btn = ft.TextButton(
        text="Voltar",
        on_click=lambda _: page.go("/administracao"),
        style=ft.ButtonStyle(color=ft.Colors.BLUE),
    )

    layout = ft.Column(
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Cadastro de Funcionário (OpenCV + Hash)", size=24, weight="bold"),
            nome_input,
            cpf_input,
            matricula_input,
            entidade_input,
            camera_feed,
            capturar_btn,
            salvar_btn,
            voltar_btn,
        ]
    )

    return ft.View(
        route="/cadastrar_funcionario",
        scroll="adaptive",
        controls=[layout],
    )
