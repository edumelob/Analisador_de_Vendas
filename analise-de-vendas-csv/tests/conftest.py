import textwrap

import pytest


@pytest.fixture
def write_csv(tmp_path):
    """Cria um CSV temporário. Uso: write_csv('conteúdo', name='x.csv', encoding='utf-8')."""

    def _write(content: str, name: str = "vendas.csv", encoding: str = "utf-8") -> str:
        path = tmp_path / name
        path.write_bytes(textwrap.dedent(content).lstrip("\n").encode(encoding))
        return str(path)

    return _write
