import socket
import os
import sys
import django
import dns.message

# Django bootstrap
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DNS.settings")
django.setup()

from dnsserver.handler import handle_query

DNS_PORT = 8053
BUFFER_SIZE = 512

def start_udp_dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", DNS_PORT))

    print(f"🚀 DNS Server running on UDP port {DNS_PORT}")

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        try:
            dns_request = dns.message.from_wire(data)
            response = handle_query(dns_request=dns_request)
            sock.sendto(response, addr)
        except Exception as e:
            print(f"❌ DNS error from {addr}: {e}")

if __name__ == "__main__":
    start_udp_dns_server()
