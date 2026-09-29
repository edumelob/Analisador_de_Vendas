import json

from sales_analyzer.cli import main

VALID = "produto,quantidade,preco\nMouse,4,50.00\nMonitor,1,900.00\n"


def test_success_prints_report(write_csv, capsys):
    assert main([write_csv(VALID)]) == 0
    out = capsys.readouterr().out
    assert "R$ 1.100,00" in out and "Mouse" in out


def test_file_not_found(capsys):
    assert main(["nao_existe.csv"]) == 1
    assert "não encontrado" in capsys.readouterr().err


def test_invalid_rows_warn_but_succeed(write_csv, capsys):
    assert main([write_csv(VALID + "Fone,x,10\n")]) == 0
    captured = capsys.readouterr()
    assert "linha 4" in captured.err and "ignorada" in captured.err
    assert "R$ 1.100,00" in captured.out


def test_strict_mode_fails_on_invalid_rows(write_csv, capsys):
    assert main([write_csv(VALID + "Fone,x,10\n"), "--strict"]) == 1
    assert "--strict" in capsys.readouterr().err


def test_no_valid_sales(write_csv, capsys):
    assert main([write_csv("produto,quantidade,preco\nA,x,y\n")]) == 1
    assert "nenhuma venda válida" in capsys.readouterr().err


def test_missing_columns(write_csv, capsys):
    assert main([write_csv("a,b\n1,2\n")]) == 1
    assert "Colunas obrigatórias" in capsys.readouterr().err


def test_exports(write_csv, tmp_path, capsys):
    json_path = tmp_path / "sub" / "resumo.json"
    md_path = tmp_path / "relatorio.md"
    code = main([write_csv(VALID), "--export-json", str(json_path), "--export-md", str(md_path)])
    assert code == 0
    assert json.loads(json_path.read_text(encoding="utf-8"))["revenue"] == "1100.00"
    assert md_path.read_text(encoding="utf-8").startswith("# Análise de Vendas")


def test_export_to_unwritable_path_returns_error(write_csv, tmp_path, capsys):
    blocker = tmp_path / "arquivo"
    blocker.write_text("x")
    assert main([write_csv(VALID), "--export-json", str(blocker / "out.json")]) == 1
    assert "Erro ao salvar" in capsys.readouterr().err


def test_invalid_top_is_rejected(write_csv, capsys):
    try:
        main([write_csv(VALID), "--top", "0"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("esperava SystemExit(2)")
