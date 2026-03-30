import socket


def is_port_available(port):
    """Controleer of een poort beschikbaar is."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False
