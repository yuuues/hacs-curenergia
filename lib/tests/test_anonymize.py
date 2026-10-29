import io
import sys

import pytest
from anonymize import (
    apply_replacements,
    drop_noise_lines,
    find_leaks,
    load_secrets,
    main,
    mask_nif,
)


def test_drops_barcode_and_glyph_lines():
    text = (
        "A\n"
        "9050712345678901234567890123456789012345678901\n"
        "ƼžƚƚƚžƼĽƁƂƃƄƅ\n"
        "ÕÆ»£¢«ÀÊ¿©¨³Ö\n"
        "Ļüá×ìļ\n"
        "kh\t1e) MXH\tH>,m\n"
        "k[4Q98@_SP.]=]Ll\n"
        "B"
    )

    assert drop_noise_lines(text) == "A\nB"


@pytest.mark.parametrize(
    "line",
    [
        "Página   1 / 4",
        "83100021",
        "IVA 21 % s/84,63 € 17,77 €",
        "inscripción 1ª - CIF A-95554630",
    ],
)
def test_keeps_normal_lines(line):
    assert drop_noise_lines(line) == line


def test_keeps_page_separator_when_dropping_glyph_line():
    # pypdf pega el final de una página y el principio de la siguiente en una línea.
    text = 'A\n"\fĻüá×ìļ\nB'

    assert drop_noise_lines(text) == 'A\n"\fB'


def test_drop_extra_patterns():
    text = "uno\nOficina secreta 12\ndos"

    assert drop_noise_lines(text, [r"^Oficina"]) == "uno\ndos"


def test_replacements_longest_first():
    mapping = {"ES 0031 1": "X", "ES 0031": "Y"}

    assert apply_replacements("ES 0031 1 y ES 0031", mapping) == "X y Y"


def test_nif_masked():
    assert mask_nif("NIF:  12345678Z") == "NIF:  00000000T"


def test_find_leaks_detects_value_without_spaces():
    mapping = {"ES 0031 9999": "F"}

    assert find_leaks("línea\nES00319999", mapping) == [(2, "ES 0031 9999")]


def test_find_leaks_detects_unmasked_nif():
    assert find_leaks("NIF 00000000T\nNIF 12345678Z", {}) == [(2, "12345678Z")]


@pytest.mark.parametrize(
    "text",
    [
        "uno\nES 0031\n9999 dos",
        "uno\nES\t0031\xa09999",
        "uno\nES 00\f31 9999",
        "uno\nes 0031\n  99\n99",
    ],
    ids=["newline", "tab-nbsp", "formfeed", "several-lines"],
)
def test_find_leaks_detects_value_split_across_lines(text):
    assert find_leaks(text, {"ES 0031 9999": "F"}) == [(2, "ES 0031 9999")]


def test_find_leaks_reports_each_leak_once():
    assert find_leaks("ES00319999", {"ES 0031 9999": "F"}) == [(1, "ES 0031 9999")]


def _write(path, content: str):
    path.write_text(content, encoding="utf-8")
    return path


def test_check_report_never_prints_real_values(tmp_path, monkeypatch):
    secrets = _write(
        tmp_path / "secrets.toml",
        '[replace]\n"Otro valor" = "X"\n"Nombre Secreto" = "NOMBRE"\n',
    )
    fixture = _write(tmp_path / "f.txt", "a\nNombre\nSecreto\nNIF 12345678Z\n")
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)

    assert main(["--check", str(fixture), "--secrets", str(secrets)]) == 1

    report = stderr.getvalue()
    for real in ("Nombre", "Secreto", "12345678", "Otro valor"):
        assert real not in report
    assert f"{fixture}:2: clave nº 2 de [replace]" in report
    assert f"{fixture}:4: NIF sin enmascarar" in report


def test_check_works_when_stderr_has_no_reconfigure(tmp_path, monkeypatch):
    secrets = _write(tmp_path / "secrets.toml", '[replace]\n"real" = "falso"\n')
    fixture = _write(tmp_path / "f.txt", "falso\n")
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    assert main(["--check", str(fixture), "--secrets", str(secrets)]) == 0


@pytest.mark.parametrize(
    "content",
    [
        'replace = "no es una tabla"\n',
        '[replace]\n"" = "falso"\n',
        '[replace]\n"real" = ""\n',
        '[replace]\n"real" = 1\n',
        '[drop]\npatterns = "no es una lista"\n',
        "[drop]\npatterns = [1]\n",
    ],
)
def test_load_secrets_rejects_invalid_file(tmp_path, content):
    path = _write(tmp_path / "secrets.toml", content)

    with pytest.raises(ValueError, match="secrets"):
        load_secrets(path)


def test_load_secrets_error_does_not_echo_values(tmp_path):
    path = _write(tmp_path / "secrets.toml", '[replace]\n"VALOR REAL" = ""\n')

    with pytest.raises(ValueError) as excinfo:
        load_secrets(path)

    assert "VALOR REAL" not in str(excinfo.value)


def test_load_secrets_valid(tmp_path):
    path = _write(
        tmp_path / "secrets.toml",
        '[replace]\n"real" = "falso"\n[drop]\npatterns = ["^x"]\n',
    )

    assert load_secrets(path) == ({"real": "falso"}, ["^x"])
