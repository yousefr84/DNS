import os
import socket
import sys
import threading

import django
import dns.message

# -----------------------------
# Django bootstrap
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DNS.settings")
django.setup()

from dnsserver.handler import handle_query

DNS_PORT = 8053
BUFFER_SIZE = 4096


# -----------------------------
# UDP DNS Server
# -----------------------------
def start_udp_dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", DNS_PORT))
    print(f"🚀 DNS UDP Server running on port {DNS_PORT}")

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        try:
            dns_request = dns.message.from_wire(data)
            response = handle_query(dns_request=dns_request)
            sock.sendto(response, addr)
        except Exception as e:
            print(f"❌ UDP DNS error from {addr}: {e}")


# -----------------------------
# TCP DNS Server
# -----------------------------
def handle_tcp_client(conn, addr):
    try:
        length_bytes = conn.recv(2)
        if not length_bytes:
            return

        length = int.from_bytes(length_bytes, "big")
        data = conn.recv(length)

        dns_request = dns.message.from_wire(data)
        response = handle_query(dns_request=dns_request)

        conn.sendall(len(response).to_bytes(2, "big") + response)

    except Exception as e:
        print(f"❌ TCP DNS error from {addr}: {e}")
    finally:
        conn.close()


def start_tcp_dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", DNS_PORT))
    sock.listen(5)
    print(f"🚀 DNS TCP Server running on port {DNS_PORT}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(
            target=handle_tcp_client,
            args=(conn, addr),
            daemon=True
        ).start()


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=start_udp_dns_server, daemon=True).start()
    threading.Thread(target=start_tcp_dns_server, daemon=True).start()

    print("✅ DNS Server (UDP + TCP) started")
    while True:
        pass
