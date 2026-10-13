import pytest

from app.services.players import RiotIdInvalido, normalizar_riot_id


@pytest.mark.parametrize(
    ("nome", "tag", "esperado"),
    [
        ("Fulano", "BR1", ("Fulano", "BR1")),
        ("  Fulano de   Tal  ", " BR 1 ", ("Fulano de Tal", "BR1")),
        ("Fulano", "#BR1", ("Fulano", "BR1")),
    ],
)
def test_normaliza(nome, tag, esperado):
    assert normalizar_riot_id(nome, tag) == esperado


@pytest.mark.parametrize(("nome", "tag"), [("   ", "BR1"), ("Fulano", ""), ("x" * 33, "BR1")])
def test_rejeita_invalidos(nome, tag):
    with pytest.raises(RiotIdInvalido):
        normalizar_riot_id(nome, tag)
