"""Execução da formatação com tempo-limite real.

No modo "processo", cada formatação roda num processo Python próprio
(`python -m formata.trabalhador`), que recebe o documento pela entrada padrão
e devolve o resultado pela saída padrão. Se o tempo-limite estourar, o
processo é encerrado: nenhum documento malformado prende o servidor. O
conteúdo vive só na memória desse processo e some com ele.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import formata
from formata import formatar

PASTA_BACKEND = str(Path(formata.__file__).resolve().parents[1])


class TempoEsgotado(Exception):
    pass


class FalhaExecucao(Exception):
    pass


def executar(texto: str, modo: str, limites: dict[str, int], tempo_limite: float, isolamento: str) -> dict:
    if isolamento == "direto":
        return formatar(texto, modo, **limites).como_dict()

    pedido = json.dumps({"texto": texto, "modo": modo, "limites": limites}, ensure_ascii=False).encode("utf-8")
    ambiente = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": PASTA_BACKEND,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "formata.trabalhador"],
            input=pedido,
            capture_output=True,
            timeout=tempo_limite,
            env=ambiente,
            cwd=PASTA_BACKEND,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TempoEsgotado() from exc
    if proc.returncode != 0:
        # Só a última linha do erro (tipo da exceção); o conteúdo do documento não vai para o log.
        ultima = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or ["sem detalhe"]
        raise FalhaExecucao(f"trabalhador saiu com código {proc.returncode}: {ultima[0].split(':')[0]}")
    try:
        return json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FalhaExecucao("resposta do trabalhador ilegível") from exc
