
import socket
import threading
import time
import pytest
from src.servidor import iniciar_servidor, correr_servidor


# ─── Fixture: levanta y baja el servidor automáticamente ────────────────────

@pytest.fixture
def servidor_activo():
    """
    Levanta el servidor en un thread aparte usando puerto dinámico.
    Usa una flag para detenerlo limpiamente al terminar cada test (evita warnings en Windows).
    """
    srv, chat = iniciar_servidor(host="127.0.0.1", port=0)  # puerto 0 = SO elige uno libre
    puerto = srv.getsockname()[1]
    flag = [True]

    hilo = threading.Thread(target=correr_servidor, args=(srv, chat, flag), daemon=True)
    hilo.start()
    time.sleep(0.1)  # pequeña espera para que el servidor este listo

    yield puerto  # los tests reciben el puerto real

    flag[0] = False   # le avisa al loop que pare
    time.sleep(0.6)   # espera que el loop salga limpiamente
    srv.close()


def conectar(puerto):
    """Helper para crear un cliente conectado."""
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.settimeout(2)
    c.connect(("127.0.0.1", puerto))
    return c


# ─── Pruebas de conexion ─────────────────────────────────────────────────────

def test_servidor_acepta_una_conexion(servidor_activo):
    """Caso positivo: un cliente puede conectarse sin error."""
    cliente = conectar(servidor_activo)
    assert cliente.fileno() != -1
    cliente.close()


def test_servidor_acepta_multiples_conexiones(servidor_activo):
    """Caso positivo: varios clientes se conectan al mismo tiempo."""
    clientes = [conectar(servidor_activo) for _ in range(5)]
    for c in clientes:
        assert c.fileno() != -1
    for c in clientes:
        c.close()


# ─── Pruebas de mensajes ─────────────────────────────────────────────────────

def test_mensaje_llega_a_otros_clientes(servidor_activo):
    """Caso positivo: el mensaje de A llega a B."""
    cliente_a = conectar(servidor_activo)
    cliente_b = conectar(servidor_activo)
    time.sleep(0.1)

    cliente_a.send(b"Hola desde A\n")
    time.sleep(0.2)

    datos = cliente_b.recv(1024)
    assert b"Hola desde A" in datos

    cliente_a.close()
    cliente_b.close()


def test_mensaje_no_se_duplica(servidor_activo):
    """Caso negativo: el remitente no recibe su propio mensaje."""
    cliente_a = conectar(servidor_activo)
    cliente_b = conectar(servidor_activo)
    time.sleep(0.1)

    cliente_a.send(b"Solo para B\n")
    time.sleep(0.2)

    datos_b = cliente_b.recv(1024)
    assert b"Solo para B" in datos_b

    cliente_a.settimeout(0.3)
    try:
        datos_a = cliente_a.recv(1024)
        assert b"Solo para B" not in datos_a
    except socket.timeout:
        pass  # timeout = no llego nada, correcto

    cliente_a.close()
    cliente_b.close()


def test_mensajes_multiples_clientes_simultaneos(servidor_activo):
    """Caso positivo: tres clientes envian, los otros dos reciben cada mensaje."""
    clientes = [conectar(servidor_activo) for _ in range(3)]
    time.sleep(0.1)

    recibidos = {i: [] for i in range(3)}

    def recibir(idx, sock):
        try:
            while True:
                sock.settimeout(0.5)
                data = sock.recv(1024)
                if data:
                    recibidos[idx].append(data)
        except:
            pass

    hilos = [threading.Thread(target=recibir, args=(i, c), daemon=True)
                for i, c in enumerate(clientes)]
    for h in hilos:
        h.start()

    clientes[0].send(b"Mensaje de 0\n")
    clientes[1].send(b"Mensaje de 1\n")
    clientes[2].send(b"Mensaje de 2\n")
    time.sleep(0.5)

    todos_0 = b"".join(recibidos[0])
    assert b"Mensaje de 1" in todos_0
    assert b"Mensaje de 2" in todos_0

    for c in clientes:
        c.close()


def test_mensaje_vacio_no_se_reenvía(servidor_activo):
    """Caso negativo: un mensaje vacio no debe llegar a otros clientes."""
    cliente_a = conectar(servidor_activo)
    cliente_b = conectar(servidor_activo)
    time.sleep(0.1)

    cliente_a.send(b"   \n")
    time.sleep(0.2)

    cliente_b.settimeout(0.3)
    try:
        datos = cliente_b.recv(1024)
        assert datos.strip() != b""
    except socket.timeout:
        pass

    cliente_a.close()
    cliente_b.close()


# ─── Pruebas de desconexion abrupta ──────────────────────────────────────────

def test_servidor_sigue_tras_desconexion_abrupta(servidor_activo):
    """El servidor no se cae cuando un cliente se desconecta sin avisar."""
    cliente_a = conectar(servidor_activo)
    cliente_b = conectar(servidor_activo)
    time.sleep(0.1)

    cliente_a.close()
    time.sleep(0.2)

    cliente_b.send(b"Sigo vivo\n")
    time.sleep(0.1)

    cliente_c = conectar(servidor_activo)
    assert cliente_c.fileno() != -1

    cliente_b.close()
    cliente_c.close()


def test_multiples_desconexiones_abruptas(servidor_activo):
    """El servidor aguanta que varios clientes se caigan a la vez."""
    clientes = [conectar(servidor_activo) for _ in range(4)]
    time.sleep(0.1)

    for c in clientes[:3]:
        c.close()
    time.sleep(0.3)

    clientes[3].send(b"Sobrevivi\n")
    time.sleep(0.1)

    nuevo = conectar(servidor_activo)
    assert nuevo.fileno() != -1

    clientes[3].close()
    nuevo.close()


def test_mensajes_no_se_pierden_con_desconexion(servidor_activo):
    """Los mensajes entre clientes activos llegan aunque otro se haya caido."""
    cliente_a = conectar(servidor_activo)
    cliente_b = conectar(servidor_activo)
    cliente_c = conectar(servidor_activo)
    time.sleep(0.1)

    cliente_c.close()
    time.sleep(0.2)

    cliente_a.send(b"Mensaje post-caida\n")
    time.sleep(0.2)

    datos = cliente_b.recv(1024)
    assert b"Mensaje post-caida" in datos

    cliente_a.close()
    cliente_b.close()
