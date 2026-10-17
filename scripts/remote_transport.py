"""Bounded HTTPS reads with approved hosts and a pinned public destination IP."""
from __future__ import annotations
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit


class PublicHTTPS(http.client.HTTPSConnection):
    def connect(self):
        addresses = socket.getaddrinfo(self.host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('non-public DNS destination')
        # Pin the address checked above; retain hostname verification and TLS SNI.
        sock = socket.create_connection((addresses[0][4][0], 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def approved_url(url: str, hosts: list[str]):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname not in hosts or parts.username is not None
            or parts.password is not None or parts.port not in (None, 443)
            or parts.query or parts.fragment or '\\' in url
            or any(c.isspace() or ord(c) < 32 for c in url)):
        raise ValueError('destination outside approved HTTPS policy')
    return parts


def download(url: str, hosts: list[str], limit: int, timeout: int) -> str:
    deadline = time.monotonic() + timeout
    for _ in range(4):
        parts = approved_url(url, hosts)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('source deadline exceeded')
        connection = PublicHTTPS(parts.hostname, timeout=remaining, context=ssl.create_default_context())
        try:
            connection.request('GET', parts.path or '/', headers={
                'User-Agent': 'tv-playlist-automation/1.0', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                destination = response.getheader('Location')
                if not destination:
                    raise ValueError('redirect without destination')
                url = urljoin(url, destination)
                continue
            if response.status != 200:
                # No retries of 403/429 or other failures, no credentials in errors.
                raise ValueError(f'HTTP {response.status}')
            size = response.getheader('Content-Length')
            if size and int(size) > limit:
                raise ValueError('source size limit')
            data = bytearray()
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('source deadline exceeded')
                if connection.sock:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(65536, limit + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError('source size limit')
            return data.decode('utf-8-sig')
        finally:
            connection.close()
    raise ValueError('redirect limit')
