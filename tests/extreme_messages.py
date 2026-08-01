#!/usr/bin/env python3
"""
Executa requests direcionados com mensagens extremas (vazias, muito longas ou
desorganizadas) para validar o endpoint de chat.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Iterable, List
from uuid import uuid4

import aiohttp

from tests.many_requests import (
    DEFAULT_URL,
    RequestResult,
    print_request_log,
    send_request,
    summarize,
)


EXTREME_MESSAGES = [
    "",
    "     ",
    "???",
    "!@#$%^&*()_+=-[]{};:',.<>/?|`~",
    "dXJlIGFic3VyZG8gcXVlIHR1ZG8gZXN0YSBmdW5jaW9uYW5kbyBkbyBncmFucmUgaW5mb3Jt"
    "YcOnw6NvIG51bmNhIGVmZXRpdmE/ significaria algo?",
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua?",
    "Preciso saber se voce >>>>>>>>>>>> ................ ########### agora?",
    "DROP TABLE pacientes; --",
    " ".join("token" for _ in range(200)),
    "A" * 2048,
]


def build_message_pool(extra_messages: Iterable[str] | None) -> List[str]:
    pool = list(EXTREME_MESSAGES)
    if extra_messages:
        for message in extra_messages:
            if message is None:
                continue
            pool.append(str(message))
    return pool


async def run_extreme_messages(
    url: str,
    pause: float,
    timeout: float,
    cycles: int,
    extra_messages: Iterable[str] | None,
) -> List[RequestResult]:
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    results: List[RequestResult] = []
    messages = build_message_pool(extra_messages)

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        index = 0
        for cycle in range(cycles):
            for message in messages:
                session_id = str(uuid4())
                result = await send_request(
                    session=session,
                    url=url,
                    session_id=session_id,
                    message=message,
                    index=index,
                )
                results.append(result)
                index += 1

                if pause > 0:
                    await asyncio.sleep(pause)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testa o endpoint com mensagens extremas."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_URL,
        help=f"URL do endpoint (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=2,
        help="Numero de ciclos completos sobre o conjunto de mensagens.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.0,
        help="Intervalo em segundos entre os requests.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout total de cada request.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Mensagem adicional a ser incluida (pode repetir a flag).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nao exibe o log de cada request.",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()

    if args.cycles <= 0:
        raise ValueError("--cycles deve ser maior que zero")

    results = await run_extreme_messages(
        url=args.base_url,
        pause=args.pause,
        timeout=args.timeout,
        cycles=args.cycles,
        extra_messages=args.include,
    )

    if not args.quiet:
        for result in results:
            print_request_log(result)

    summarize(results)


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nExecucao interrompida pelo usuario.")


if __name__ == "__main__":
    main()

