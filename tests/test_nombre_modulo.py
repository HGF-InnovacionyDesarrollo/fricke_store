"""Regla de la Unidad (18 nov 2026): el nombre de todo módulo es «F+» y su nombre corto, en minúsculas."""
import pytest

from logo_modulo import problemas_nombre


@pytest.mark.parametrize("nombre", ["F+data", "F+avisos", "F+farmacia", "F+caídas", "F+uci2"])
def test_nombres_validos(nombre):
    assert problemas_nombre(nombre) == []


@pytest.mark.parametrize("nombre", ["Farmacia", "F+Data", "f+data", "F+ data", "F+data turnos", "F+", "Data+", "F+app"])
def test_nombres_invalidos(nombre):
    assert problemas_nombre(nombre)
