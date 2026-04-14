# tests/test_unitario.py
import pytest
from unittest.mock import MagicMock
from src.manager import ChatManager


# ─── Validación de mensajes (TDD: Red → Green → Refactor) ───────────────────

def test_mensaje_valido_normal():
    """Caso positivo: mensaje con texto normal."""
    manager = ChatManager()
    assert manager.es_mensaje_valido("Hola") is True

def test_mensaje_valido_con_espacios_internos():
    """Caso positivo: mensaje con espacios en el medio."""
    manager = ChatManager()
    assert manager.es_mensaje_valido("Hola mundo") is True

def test_mensaje_vacio_es_invalido():
    """Caso negativo TDD: string vacío debe rechazarse."""
    manager = ChatManager()
    assert manager.es_mensaje_valido("") is False

def test_mensaje_solo_espacios_es_invalido():
    """Caso negativo TDD: solo espacios debe rechazarse."""
    manager = ChatManager()
    assert manager.es_mensaje_valido("   ") is False

def test_mensaje_none_es_invalido():
    """Caso negativo: None no debe romper la función."""
    manager = ChatManager()
    assert manager.es_mensaje_valido(None) is False


# ─── Gestión de clientes ─────────────────────────────────────────────────────

def test_registrar_cliente():
    """Caso positivo: el cliente queda en las listas después de registrarse."""
    manager = ChatManager()
    mock_socket = MagicMock()
    direccion = ("127.0.0.1", 5000)

    manager.registrar_cliente(mock_socket, direccion)

    assert mock_socket in manager.conexiones_activas
    assert manager.direcciones_clientes[mock_socket] == direccion

def test_eliminar_cliente():
    """Caso positivo: el cliente desaparece de las listas al eliminarse."""
    manager = ChatManager()
    mock_socket = MagicMock()
    manager.registrar_cliente(mock_socket, ("127.0.0.1", 5000))

    manager.eliminar_cliente(mock_socket)

    assert mock_socket not in manager.conexiones_activas
    assert mock_socket not in manager.direcciones_clientes

def test_eliminar_cliente_devuelve_direccion():
    """Caso positivo: eliminar retorna la dirección del cliente."""
    manager = ChatManager()
    mock_socket = MagicMock()
    direccion = ("127.0.0.1", 6000)
    manager.registrar_cliente(mock_socket, direccion)

    resultado = manager.eliminar_cliente(mock_socket)

    assert resultado == direccion

def test_eliminar_cliente_inexistente_no_falla():
    """Caso negativo: eliminar un socket que no existe no lanza excepción."""
    manager = ChatManager()
    mock_socket = MagicMock()
    # No lanza error
    manager.eliminar_cliente(mock_socket)


# ─── Obtener destinatarios ───────────────────────────────────────────────────

def test_obtener_destinatarios_excluye_origen_y_servidor():
    """El remitente y el socket servidor no deben recibir el mensaje."""
    manager = ChatManager()
    servidor_sock = MagicMock()
    origen = MagicMock()
    cliente_b = MagicMock()
    cliente_c = MagicMock()

    manager.conexiones_activas = [servidor_sock, origen, cliente_b, cliente_c]

    destinatarios = manager.obtener_destinatarios(origen, servidor_sock)

    assert origen not in destinatarios
    assert servidor_sock not in destinatarios
    assert cliente_b in destinatarios
    assert cliente_c in destinatarios

def test_obtener_destinatarios_sin_otros_clientes():
    """Si no hay más clientes, la lista de destinatarios es vacía."""
    manager = ChatManager()
    servidor_sock = MagicMock()
    origen = MagicMock()

    manager.conexiones_activas = [servidor_sock, origen]

    destinatarios = manager.obtener_destinatarios(origen, servidor_sock)

    assert destinatarios == []
