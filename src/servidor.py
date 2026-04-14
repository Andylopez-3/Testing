# src/servidor.py
import socket
import select
import threading
from .manager import ChatManager

HOST = "0.0.0.0"
PORT = 12345


def iniciar_servidor(host=HOST, port=PORT):
    """
    Levanta el servidor y retorna (servidor_socket, chat_manager).
    Separado así para que los tests puedan levantarlo y bajarlo.
    """
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, port))
    servidor.listen()

    chat = ChatManager()
    chat.conexiones_activas.append(servidor)

    return servidor, chat


def correr_servidor(servidor, chat):
    """
    Bucle principal del servidor. Bloquea hasta que el socket se cierre.
    """
    ejecutando = True

    while ejecutando:
        try:
            lectura, _, _ = select.select(chat.conexiones_activas, [], [], 1)
        except:
            break

        for sock in lectura:
            if sock == servidor:
                cliente_sock, direccion = servidor.accept()
                chat.registrar_cliente(cliente_sock, direccion)
                print(f"Conectado: {direccion}")
            else:
                try:
                    data = sock.recv(1024)
                    if not data:
                        raise Exception("Desconectado")

                    texto = data.decode().strip()
                    if chat.es_mensaje_valido(texto):
                        print(f"[{chat.direcciones_clientes[sock]}] {texto}")
                        for destino in chat.obtener_destinatarios(sock, servidor):
                            destino.send(data)
                    else:
                        print(f"Mensaje inválido de {chat.direcciones_clientes[sock]}")
                except:
                    info = chat.eliminar_cliente(sock)
                    print(f"Desconectado: {info}")

    print("Servidor fuera de servicio.")


# Solo corre si ejecutás este archivo directamente: python -m src.servidor
if __name__ == "__main__":
    servidor, chat = iniciar_servidor()

    def escuchar_consola():
        while True:
            if input().strip().lower() == "salir":
                servidor.close()
                break

    threading.Thread(target=escuchar_consola, daemon=True).start()
    print(f"Servidor escuchando en {PORT}...")
    correr_servidor(servidor, chat)
