import os
from pathlib import Path

import pytest
from ash_dal.utils import prepare_ssl_context


@pytest.fixture
def mock_server_ca() -> str:
    tests_path = Path(__file__).parent.parent
    cert_path = Path(tests_path, "test_data/server-ca.pem")
    with cert_path.open("r") as f:
        return f.read()


@pytest.fixture
def mock_client_cert() -> str:
    tests_path = Path(__file__).parent.parent
    cert_path = Path(tests_path, "test_data/client-cert.pem")
    with cert_path.open("r") as f:
        return f.read()


@pytest.fixture
def mock_client_key() -> str:
    tests_path = Path(__file__).parent.parent
    cert_path = Path(tests_path, "test_data/client-key.pem")
    with cert_path.open("r") as f:
        return f.read()


@pytest.fixture
def create_mock_certificates(
    tmp_path, mock_server_ca, mock_client_cert, mock_client_key
) -> tuple[Path, tuple[str, str, str]]:
    certs_dir = Path(tmp_path, "certificates")
    os.mkdir(certs_dir)
    entities = ("client-cert.pem", "client-key.pem", "server-ca.pem")
    entities_data = (mock_client_cert, mock_client_key, mock_server_ca)
    for entity, data in zip(entities, entities_data):
        with Path(certs_dir, entity).open("w") as f:
            f.write(data)
    return certs_dir, entities


def test_prepare_ssl_context(create_mock_certificates):
    certs_dir, entities = create_mock_certificates
    result = prepare_ssl_context(
        client_cert_path=entities[0],
        client_key_path=entities[1],
        server_ca_path=entities[2],
        ssl_root_dir=certs_dir,
    )
    assert result


def test_prepare_ssl_context__full_file_paths(create_mock_certificates):
    certs_dir, entities = create_mock_certificates
    result = prepare_ssl_context(
        client_cert_path=Path(certs_dir, entities[0]),
        client_key_path=Path(certs_dir, entities[1]),
        server_ca_path=Path(certs_dir, entities[2]),
    )
    assert result
