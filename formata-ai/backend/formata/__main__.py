"""Linha de comando: python -m formata documento.md [--modo auto|markdown|html] [--json]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .motor import formatar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formata", description="Formata.AI — paginação e marcação HTML.")
    parser.add_argument("arquivo", help="arquivo .md, .txt ou .html; use - para ler da entrada padrão")
    parser.add_argument("--modo", choices=["auto", "markdown", "html"], default="auto")
    parser.add_argument("--json", action="store_true", help="imprime o resultado completo em JSON")
    args = parser.parse_args(argv)

    if args.arquivo == "-":
        texto = sys.stdin.read()
    else:
        try:
            texto = Path(args.arquivo).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print("O arquivo não está em UTF-8.", file=sys.stderr)
            return 2
    resultado = formatar(texto, args.modo)

    if args.json:
        print(json.dumps(resultado.como_dict(), ensure_ascii=False, indent=2))
    elif resultado.ok:
        print(resultado.resposta)
    else:
        print(resultado.mensagem)
        for erro in resultado.erros:
            print(f"- {erro}", file=sys.stderr)
    for aviso in resultado.avisos if not args.json else []:
        print(f"Aviso: {aviso}", file=sys.stderr)
    if resultado.ok:
        return 0
    return 1 if resultado.codigo == "falha_validacao" else 2


if __name__ == "__main__":
    sys.exit(main())
