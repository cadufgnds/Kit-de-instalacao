"""Configuração do servidor, lida de variáveis de ambiente (veja .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PASTA_FRONTEND_PADRAO = Path(__file__).resolve().parents[2] / "frontend"
EXTENSOES_ACEITAS = (".md", ".markdown", ".txt", ".html", ".htm")


def _int(nome: str, padrao: int) -> int:
    valor = os.environ.get(nome, "").strip()
    return int(valor) if valor else padrao


def _float(nome: str, padrao: float) -> float:
    valor = os.environ.get(nome, "").strip()
    return float(valor) if valor else padrao


def _bool(nome: str, padrao: bool) -> bool:
    valor = os.environ.get(nome, "").strip().lower()
    return padrao if not valor else valor in ("1", "true", "sim", "yes", "on")


@dataclass(frozen=True)
class Configuracao:
    limite_bytes: int = 1_048_576  # tamanho máximo do documento (UTF-8)
    limite_linhas: int = 20_000
    tempo_limite: float = 15.0  # segundos por formatação
    max_processos: int = field(default_factory=lambda: os.cpu_count() or 2)
    isolamento: str = "processo"  # "processo" (recomendado) ou "direto"
    pasta_frontend: Path | None = PASTA_FRONTEND_PADRAO
    origens_cors: tuple[str, ...] = ()
    docs_api: bool = True
    nivel_log: str = "INFO"

    @classmethod
    def do_ambiente(cls) -> "Configuracao":
        pasta = os.environ.get("FORMATA_FRONTEND_DIR")
        origens = os.environ.get("FORMATA_ORIGENS_CORS", "")
        return cls(
            limite_bytes=_int("FORMATA_LIMITE_BYTES", cls.limite_bytes),
            limite_linhas=_int("FORMATA_LIMITE_LINHAS", cls.limite_linhas),
            tempo_limite=_float("FORMATA_TEMPO_LIMITE", cls.tempo_limite),
            max_processos=_int("FORMATA_MAX_PROCESSOS", os.cpu_count() or 2),
            isolamento=os.environ.get("FORMATA_ISOLAMENTO", cls.isolamento),
            pasta_frontend=Path(pasta) if pasta else PASTA_FRONTEND_PADRAO,
            origens_cors=tuple(o.strip() for o in origens.split(",") if o.strip()),
            docs_api=_bool("FORMATA_DOCS_API", cls.docs_api),
            nivel_log=os.environ.get("FORMATA_LOG_NIVEL", cls.nivel_log).upper(),
        )

    @property
    def limite_corpo_requisicao(self) -> int:
        """Corpo HTTP aceito: o documento mais a sobrecarga de JSON ou multipart."""
        return 2 * self.limite_bytes + 64 * 1024
