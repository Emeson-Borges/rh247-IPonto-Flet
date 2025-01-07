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

    status_text = ft.Text("Inicializando câmera...", size=20, weight="bold", color=ft.Colors.BLUE)
    camera_feed = ft.Image(width=300, height=300)
    timer_text = ft.Text("5 segundos restantes", size=18, weight="bold", color=ft.Colors.RED)

    stop_camera = False
    identificacao_realizada = False

    # Tolerância de bits para considerar dois hashes pHash como iguais.
    # Se estiver muito baixo (por ex. 5), é muito estrito; se estiver muito alto (20+), vira “qualquer pessoa”.
    PHASH_THRESHOLD = 15

    def emitir_alerta(titulo, mensagem):
        """Exibe um alerta e volta para a tela inicial."""
        def fechar_dialog(e):
            page.dialog.open = False
            page.go("/")
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(titulo),
            content=ft.Text(mensagem),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    def exibir_confirmacao(mensagem):
        """Exibe mensagem de sucesso e volta para a tela inicial."""
        def fechar_dialog(e):
            page.dialog.open = False
            page.go("/")
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Sucesso"),
            content=ft.Text(mensagem),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)],
        )
        page.dialog.open = True
        page.update()

    def registrar_ponto(conn, funcionario_id):
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
        except Exception as e:
            emitir_alerta("Erro", f"Erro ao registrar ponto: {e}")

    # =============== LÓGICA DO pHASH ====================

    def gerar_phash(bgr_image):
        """
        Gera o hash pHash (64 bits = 8 bytes) com OpenCV (opencv-contrib).
        Antes, normaliza a iluminação com equalização de histograma.
        Retorna um array shape(1,8).
        """
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        # Normaliza iluminação
        gray = cv2.equalizeHist(gray)

        hasher = cv2.img_hash.PHash_create()  # requer opencv-contrib
        hash_val = hasher.compute(gray)       # shape: (1,8)
        return hash_val

    def distance_hash(hash1, hash2):
        """
        Compara 2 hashes pHash (cada um shape(1,8)) bit a bit.
        Retorna o número de bits diferentes (Hamming distance).
        """
        b1 = hash1.tobytes()
        b2 = hash2.tobytes()
        diff_bits = 0
        for bb1, bb2 in zip(b1, b2):
            xor_val = bb1 ^ bb2
            diff_bits += bin(xor_val).count("1")
        return diff_bits

    # ======================================================

    def update_images():
        """
        Captura frames ao longo de 5s, gera pHash do rosto, compara e pega o MENOR 'diff' obtido.
        Se menor diff <= PHASH_THRESHOLD, considera reconhecido.
        """
        nonlocal stop_camera, identificacao_realizada

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            status_text.value = "Erro: Não foi possível acessar a câmera."
            status_text.color = ft.Colors.RED
            page.update()
            return

        status_text.value = "Câmera iniciada. Posicione seu rosto."
        status_text.color = ft.Colors.GREEN
        page.update()

        start_time = time.time()
        capture_duration = 5  # Tentar por 5 segundos

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # Vamos ficar salvando o MENOR diff encontrado para cada funcionário, e se ficar abaixo do threshold, paramos
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
                # recorta a área do rosto
                rosto_capturado = frame[y : y + h, x : x + w]

                # Gera o pHash do rosto atual
                hash_atual = gerar_phash(rosto_capturado)

                # Percorre TODOS funcionários no BD e compara
                cursor.execute(
                    """
                    SELECT funcionario_id, nome, matricula, embedding, foto_base64
                    FROM funcionarios
                    """
                )
                funcionarios = cursor.fetchall()

                for (func_id, nome, matricula, embedding_hex, foto_b64) in funcionarios:
                    # Se não tiver hash no BD, ignora
                    if not embedding_hex:
                        continue

                    try:
                        stored_bytes = bytes.fromhex(embedding_hex)
                        stored_hash = np.frombuffer(stored_bytes, dtype=np.uint8).reshape((1, 8))

                        diff = distance_hash(hash_atual, stored_hash)
                        print(f"[DEBUG] {nome} (id={func_id}), diff={diff}")

                        # Se for o MENOR diff que vimos até agora, guardamos
                        if melhor_diff_global is None or diff < melhor_diff_global:
                            melhor_diff_global = diff
                            melhor_funcionario = (func_id, nome, matricula)

                    except ValueError:
                        # Se esse embedding não for hex válido, ignore
                        continue

            # Desenha retângulo de feedback se há rosto
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Atualiza feed
            _, buffer = cv2.imencode(".jpg", frame)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")
            camera_feed.src_base64 = frame_base64
            page.update()

            elapsed_time = time.time() - start_time
            remaining_time = max(0, 5 - int(elapsed_time))
            timer_text.value = f"{remaining_time} segundos restantes"
            page.update()

            # Se achamos um diff abaixo do threshold, registra e encerra
            if melhor_diff_global is not None and melhor_diff_global <= PHASH_THRESHOLD:
                if not identificacao_realizada:
                    identificacao_realizada = True
                    (func_id, nome, matricula) = melhor_funcionario

                    # Registra o ponto
                    registrar_ponto(conn, func_id)

                    exibir_confirmacao(
                        f"Ponto registrado:\n"
                        f"Nome: {nome} (Matrícula: {matricula})\n"
                        f"diff={melhor_diff_global}"
                    )
                    stop_camera_feed(None)
                break

            if elapsed_time >= capture_duration and not identificacao_realizada:
                # terminou o tempo e não atingimos threshold
                if melhor_funcionario is not None:
                    # Mostramos quem foi o mais próximo, mas não atingiu threshold
                    (f_id, f_nome, f_mat) = melhor_funcionario
                    emitir_alerta(
                        "Alerta",
                        f"Funcionário não reconhecido (melhor diff={melhor_diff_global}). "
                        "Tente novamente ou contate o RH."
                    )
                else:
                    emitir_alerta("Alerta", "Nenhum rosto reconhecido. Tente novamente ou contate o RH.")
                stop_camera_feed(None)
                break

            time.sleep(0.03)

        cap.release()
        conn.close()

    def start_camera():
        nonlocal stop_camera
        stop_camera = False
        Thread(target=update_images, daemon=True).start()

    def stop_camera_feed(e):
        nonlocal stop_camera
        stop_camera = True
        status_text.value = "Câmera pausada."
        status_text.color = ft.Colors.BLUE
        page.update()

    start_camera()

    return ft.View(
        route="/registro_ponto",
        controls=[
            ft.Column(
                controls=[
                    camera_feed,
                    timer_text,
                    status_text,
                    ft.ElevatedButton(
                        text="Voltar",
                        on_click=stop_camera_feed,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.Padding(left=20, top=10, right=20, bottom=10),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
    )
