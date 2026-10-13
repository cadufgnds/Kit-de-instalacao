"""python -m servidor [--host 0.0.0.0] [--porta 8000] [--workers 2]"""

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="servidor", description="Formata.AI Web — API e landing page")
    parser.add_argument("--host", default=os.environ.get("FORMATA_HOST", "127.0.0.1"))
    parser.add_argument("--porta", type=int, default=int(os.environ.get("FORMATA_PORTA", "8000")))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("FORMATA_WORKERS", "1")))
    args = parser.parse_args()
    uvicorn.run(
        "servidor.app:criar_app",
        factory=True,
        host=args.host,
        port=args.porta,
        workers=args.workers,
        proxy_headers=True,
        server_header=False,
    )


if __name__ == "__main__":
    main()
