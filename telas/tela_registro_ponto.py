import flet as ft
import base64
from threading import Thread
import time
import sqlite3
import os
import cv2
import json
import numpy as np

DB_PATH = "banco_de_dados.db"

def criar_tela_registro_ponto(page: ft.Page, db_path: str):
    if not os.path.exists(db_path):
        raise ValueError(f"Banco de dados não encontrado no caminho: {db_path}")

    camera_feed = ft.Image(width=300, height=300)
    timer_text = ft.Text("5 segundos restantes", size=18, weight="bold", color=ft.Colors.RED)

    stop_camera = False
    identificacao_realizada = False
    PHASH_THRESHOLD = 15  # Tolerância pHash

    def emitir_alerta(titulo, mensagem):
        """
        Exibe um alerta sem o botão 'OK' persistente
        e depois de fechar, volta à tela inicial.
        """
        def fechar_dialog(e):
            page.dialog.open = False
            page.go("/")
            page.update()

        # Exibe um AlertDialog simples
        page.dialog = ft.AlertDialog(
            title=ft.Text(titulo, size=22, weight="bold"),
            content=ft.Text(mensagem, size=16),
            # Em vez de um botão de ação, poderíamos usar "on_dismiss" - mas Flet
            # não oferece isso diretamente. Então podemos colocar um "OK" pequeno:
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    def exibir_confirmacao(nome, matricula):
        """
        Exibe mensagem de sucesso com ícone de verificado, mostra Nome e Matrícula,
        e depois de 3 segundos desaparece e volta para "/".
        """
        def fechar_dialog(_):
            page.dialog.open = False
            page.go("/")
            page.update()

        # Ícone + texto
        check_icon = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Icon(name=ft.icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN, size=50),
                ft.Text(" Ponto Registrado!", size=22, weight="bold", color=ft.Colors.GREEN),
            ],
        )

        # Cria o AlertDialog
        page.dialog = ft.AlertDialog(
            title=check_icon,
            content=ft.Text(f"Nome: {nome}\nMatrícula: {matricula}", size=16),
            # Não precisamos de nenhum botão, pois vai sumir sozinho
        )
        page.dialog.open = True
        page.update()

        # Agenda o fechamento após 3 segundos
        def fechar_automatico():
            time.sleep(3)
            # Fechar e voltar ao início
            page.dialog.open = False
            page.go("/")
            page.update()

        Thread(target=fechar_automatico, daemon=True).start()

    def registrar_ponto(conn, funcionario_id, nome, matricula):
        """Registra o ponto na tabela ponto_final."""
        try:
            data_ponto = time.strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """
                INSERT INTO ponto_final (data_ponto, funcionario_vinculo_id, sincronizado)
                VALUES (?, ?, ?)
                """,
                (data_ponto, funcionario_id, 0),
            )
            conn.commit()
            exibir_confirmacao(nome, matricula)
        except Exception as e:
            emitir_alerta("Erro", f"Erro ao registrar ponto: {e}")

    # =============== pHash Lógica ====================

    def gerar_phash(bgr_image):
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        hasher = cv2.img_hash.PHash_create()
        return hasher.compute(gray)  # shape (1,8)

    def distance_hash(hash1, hash2):
        b1 = hash1.tobytes()
        b2 = hash2.tobytes()
        diff_bits = 0
        for bb1, bb2 in zip(b1, b2):
            xor_val = bb1 ^ bb2
            diff_bits += bin(xor_val).count("1")
        return diff_bits

    # =================================================

    def update_images():
        nonlocal stop_camera, identificacao_realizada

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
        except Exception as e:
            emitir_alerta("Erro", f"Falha ao conectar ao banco: {e}")
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            emitir_alerta("Erro", "Não foi possível acessar a câmera.")
            return

        start_time = time.time()
        capture_duration = 5

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        melhor_diff_global = None
        melhor_funcionario = None

        while not stop_camera:
            ret, frame = cap.read()
            if not ret:
                continue

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100),
            )

            if len(faces) > 0:
                x, y, w, h = faces[0]
                rosto_capturado = frame[y:y+h, x:x+w]

                hash_atual = gerar_phash(rosto_capturado)

                cursor.execute("SELECT funcionario_id, nome, matricula, embedding, foto_base64 FROM funcionarios")
                funcionarios = cursor.fetchall()

                for (func_id, nome, matricula, embedding_hex, foto_b64) in funcionarios:
                    if not embedding_hex:
                        continue
                    try:
                        stored_bytes = bytes.fromhex(embedding_hex)
                        stored_hash = np.frombuffer(stored_bytes, dtype=np.uint8).reshape((1, 8))

                        diff = distance_hash(hash_atual, stored_hash)
                        print(f"[DEBUG] {nome} (id={func_id}), diff={diff}")

                        if melhor_diff_global is None or diff < melhor_diff_global:
                            melhor_diff_global = diff
                            melhor_funcionario = (func_id, nome, matricula)
                    except ValueError:
                        continue

                # Desenha retângulo
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Atualiza feed
            _, buffer = cv2.imencode(".jpg", frame)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")
            camera_feed.src_base64 = frame_base64

            elapsed_time = time.time() - start_time
            remaining_time = max(0, 5 - int(elapsed_time))
            timer_text.value = f"{remaining_time} segundos restantes"

            page.update()

            # Lógica de verificação
            if melhor_diff_global is not None and melhor_diff_global <= PHASH_THRESHOLD:
                if not identificacao_realizada:
                    identificacao_realizada = True
                    (func_id, nome, mat) = melhor_funcionario

                    registrar_ponto(conn, func_id, nome, mat)
                    stop_camera = True  # Para sair do loop

            if elapsed_time >= capture_duration and not identificacao_realizada:
                # terminou o tempo e não identificou
                if melhor_funcionario is not None:
                    (f_id, f_nome, f_mat) = melhor_funcionario
                    emitir_alerta(
                        "Alerta",
                        f"Funcionário não reconhecido (diff={melhor_diff_global}). "
                        "Tente novamente ou contate o RH."
                    )
                else:
                    emitir_alerta("Alerta", "Nenhum rosto reconhecido. Tente novamente ou contate o RH.")
                stop_camera = True

            time.sleep(0.03)

        cap.release()
        conn.close()

    # Inicia a câmera automaticamente
    stop_camera = False
    Thread(target=update_images, daemon=True).start()

    # Layout centralizado: apenas feed + temporizador
    return ft.View(
        route="/registro_ponto",
        controls=[
            ft.Column(
                controls=[
                    camera_feed,
                    timer_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True,
            )
        ],
    )
