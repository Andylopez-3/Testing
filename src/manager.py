# src/manager.py

class ChatManager:
    def __init__(self):
        self.conexiones_activas = []
        self.direcciones_clientes = {}

    def es_mensaje_valido(self, texto):
        """Regla TDD: No vacíos, no solo espacios."""
        return bool(texto and texto.strip())

    def registrar_cliente(self, socket_cliente, direccion):
        self.conexiones_activas.append(socket_cliente)
        self.direcciones_clientes[socket_cliente] = direccion

    def eliminar_cliente(self, socket_cliente):
        direccion = self.direcciones_clientes.pop(socket_cliente, None)
        if socket_cliente in self.conexiones_activas:
            self.conexiones_activas.remove(socket_cliente)
        try:
            socket_cliente.close()
        except:
            pass
        return direccion

    def obtener_destinatarios(self, socket_origen, servidor_socket):
        """Retorna todos los sockets excepto el servidor y el que envía."""
        return [s for s in self.conexiones_activas
                if s != servidor_socket and s != socket_origen]
