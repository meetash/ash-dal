import ssl
from pathlib import Path


def prepare_ssl_context(
    client_cert_path: str | Path,
    client_key_path: str | Path,
    server_ca_path: str | Path,
    ssl_root_dir: str | Path | None = None,
) -> ssl.SSLContext:
    ssl_context = ssl.SSLContext()
    if ssl_root_dir:
        client_cert_path = Path(ssl_root_dir, client_cert_path)
        client_key_path = Path(ssl_root_dir, client_key_path)
        server_ca_path = Path(ssl_root_dir, server_ca_path)
    ssl_context.load_cert_chain(client_cert_path, client_key_path)
    ssl_context.load_verify_locations(server_ca_path)
    return ssl_context
