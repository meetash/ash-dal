import ssl
from pathlib import Path


def prepare_ssl_context(
    client_cert_path: str | Path,
    client_key_path: str | Path,
    server_ca_path: str | Path,
    ssl_root_dir: str | Path | None = None,
    protocol: int = ssl.PROTOCOL_TLS,
) -> ssl.SSLContext:
    """
    Creates and returns an object of :class:`ssl.SSLContext` class from key files.
    :param client_cert_path: Absolute path to client cert file. Can be relative if `sss_root_dir` parameter is passed.
    :param client_key_path: Absolute path to client key file. Can be relative if `sss_root_dir` parameter is passed.
    :param server_ca_path: Absolute path to server ca file. Can be relative if `sss_root_dir` parameter is passed.
    :param ssl_root_dir: Path to the directory with key files. If passed, you can provide relative paths to the files
    instead of absolute ones.
    :param protocol: type of protocol to be used
    :return:
    """
    ssl_context = ssl.SSLContext(protocol)
    if ssl_root_dir:
        client_cert_path = Path(ssl_root_dir, client_cert_path)
        client_key_path = Path(ssl_root_dir, client_key_path)
        server_ca_path = Path(ssl_root_dir, server_ca_path)
    ssl_context.load_cert_chain(client_cert_path, client_key_path)
    ssl_context.load_verify_locations(server_ca_path)
    return ssl_context
