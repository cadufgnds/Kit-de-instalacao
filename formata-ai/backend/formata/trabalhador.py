"""Processo trabalhador: lê {"texto", "modo", "limites"} em JSON na entrada padrão e
escreve o resultado em JSON na saída padrão. Usado pelo servidor para isolar cada
formatação num processo próprio, com tempo-limite e sem estado compartilhado."""

import json
import sys

from .motor import formatar


def main() -> int:
    pedido = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    resultado = formatar(pedido["texto"], pedido.get("modo", "auto"), **pedido.get("limites", {}))
    sys.stdout.buffer.write(json.dumps(resultado.como_dict(), ensure_ascii=False).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
