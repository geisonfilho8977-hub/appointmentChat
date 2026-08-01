#!/usr/bin/env python3
"""
Script utilitario para enviar muitas mensagens ao endpoint do chat e levantar metricas
com mensagens do ponto de vista do medico (o LLM atua como paciente).

Exemplo de uso:
    python tests/many_requests.py --total 30 --pause 0.2
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import statistics
import textwrap
from collections import Counter
from dataclasses import dataclass
from time import perf_counter
from typing import List
from uuid import uuid4

import aiohttp

DEFAULT_URL = os.environ.get("CHAT_API_URL", "http://localhost:8000/chat/chat")

DOCTOR_GREETINGS = [
    "Bom dia! Aqui e o dr. virtual acompanhando voce hoje, tudo bem?",
    "Boa tarde! Vamos revisar como seus sintomas evoluiram desde ontem?",
    "Ola! Dra. virtual passando para saber rapidamente como voce esta.",
]

SYMPTOM_CHECKS = [
    "Voce ainda sente dor latejante nos olhos quando fica em ambientes claros?",
    "A febre segue piorando no fim da tarde ou percebeu mudanca recente?",
    "As articulacoes continuam rigidas ao acordar ou estao mais soltas?",
    "Os enjoos aparecem apos as refeicoes ou surgem em horarios aleatorios?",
]

DOCTOR_TIPS = [
    "Mantenha hidratacao constante e evite excesso de cafeina hoje.",
    "Registre a pressao a cada duas horas para avaliarmos padroes.",
    "Pausa os exercicios intensos ate concluirmos os exames complementares.",
]

DIAGNOSTIC_QUESTIONS = [
    "Estou considerando {symptom}; voce percebe congestao ou dor facial?",
    "Faria sentido investigarmos {symptom} com exames laboratoriais adicionais?",
    "Voce notou sinais que apontem para {symptom} ou algo distinto?",
]

SMALL_TALK = [
    "Entre uma consulta e outra gosto de saber como voce lida com o tratamento.",
    "O clima esfriou bastante, por isso quero garantir que sua respiracao siga estavel.",
    "Tenho sugerido tecnicas de respiracao guiada; voce ja experimentou alguma?",
]

FOLLOW_UPS = [
    "Anotei que reduzir leite ajudou; continue observando essa relacao com a dor.",
    "Se precisar viajar, posso ajustar as orientacoes para o novo horario.",
    "Dormir mais cedo parece estar ajudando, mantenha essa rotina por enquanto.",
]

SYMPTOM_KEYWORDS = [
    "sinusite",
    "enxaqueca",
    "gastrite",
    "hipertensao",
    "bronquite",
    "ansiedade",
]


@dataclass
class RequestResult:
    index: int
    session_id: str
    message: str
    success: bool
    status: int | None = None
    elapsed: float | None = None
    error: str | None = None
    response_excerpt: str | None = None


def build_message(idx: int) -> str:
    """Gera mensagens variadas simulando um medico conversando com o paciente."""
    bucket = random.choice(
        ["greeting", "symptom", "doctor_tip", "diagnostic", "small_talk", "follow_up"]
    )

    if bucket == "greeting":
        return random.choice(DOCTOR_GREETINGS)
    if bucket == "symptom":
        return random.choice(SYMPTOM_CHECKS)
    if bucket == "doctor_tip":
        return random.choice(DOCTOR_TIPS)
    if bucket == "diagnostic":
        return random.choice(DIAGNOSTIC_QUESTIONS).format(
            symptom=random.choice(SYMPTOM_KEYWORDS)
        )
    if bucket == "small_talk":
        return random.choice(SMALL_TALK)

    return random.choice(FOLLOW_UPS)


async def send_request(
    session: aiohttp.ClientSession,
    url: str,
    session_id: str,
    message: str,
    index: int,
) -> RequestResult:
    payload = {"session_id": session_id, "message": message}
    started = perf_counter()

    try:
        async with session.post(url, json=payload) as response:
            elapsed = perf_counter() - started
            body_text = await _extract_body(response)
            success = 200 <= response.status < 300

            return RequestResult(
                index=index,
                session_id=session_id,
                message=message,
                success=success,
                status=response.status,
                elapsed=elapsed,
                error=None if success else body_text,
                response_excerpt=body_text if success else None,
            )
    except asyncio.TimeoutError:
        return RequestResult(
            index=index,
            session_id=session_id,
            message=message,
            success=False,
            error="timeout",
        )
    except aiohttp.ClientError as exc:
        return RequestResult(
            index=index,
            session_id=session_id,
            message=message,
            success=False,
            error=f"client-error: {exc}",
        )
    except Exception as exc:  # pragma: no cover - fallback
        return RequestResult(
            index=index,
            session_id=session_id,
            message=message,
            success=False,
            error=f"unexpected: {exc}",
        )


async def _extract_body(response: aiohttp.ClientResponse) -> str:
    try:
        data = await response.json()
        if isinstance(data, dict):
            value = data.get("message") or data
            return str(value)
        return str(data)
    except aiohttp.ContentTypeError:
        return await response.text()


async def run_stress_test(
    total_requests: int,
    url: str,
    change_session_every: int,
    pause: float,
    timeout: float,
) -> List[RequestResult]:
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    results: List[RequestResult] = []
    current_session = str(uuid4())

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        for idx in range(total_requests):
            if idx % change_session_every == 0:
                current_session = str(uuid4())

            message = build_message(idx)
            result = await send_request(
                session=session,
                url=url,
                session_id=current_session,
                message=message,
                index=idx,
            )
            results.append(result)

            if pause > 0:
                await asyncio.sleep(pause)

    return results


def print_request_log(result: RequestResult) -> None:
    status_icon = "OK" if result.success else "ERR"
    duration = (
        f"{result.elapsed * 1000:.1f} ms"
        if result.elapsed is not None
        else "--"
    )
    preview = textwrap.shorten(result.message, width=70, placeholder="...")
    extra = (
        textwrap.shorten(result.response_excerpt or "", width=60, placeholder="...")
        if result.success
        else result.error or "erro desconhecido"
    )

    print(
        f"{status_icon} #{result.index + 1:03d} "
        f"session={result.session_id[:8]} "
        f"tempo={duration} "
        f"status={result.status or 'n/a'} "
        f"msg='{preview}' "
        f"-> {extra}"
    )


def summarize(results: List[RequestResult]) -> None:
    total = len(results)
    success_latencies = [
        r.elapsed for r in results if r.success and r.elapsed is not None
    ]
    success_count = len(success_latencies)
    failure_count = total - success_count
    success_rate = (success_count / total * 100) if total else 0.0
    avg_latency = statistics.mean(success_latencies) if success_latencies else 0.0

    error_counter = Counter(r.error for r in results if r.error)

    print("\n=== Resumo ===")
    print(f"Total de requisicoes: {total}")
    print(f"Sucessos: {success_count} ({success_rate:.1f}%)")
    print(f"Falhas: {failure_count}")
    if success_latencies:
        print(f"Tempo medio de resposta: {avg_latency * 1000:.2f} ms")
    if error_counter:
        print("Principais erros:")
        for error, count in error_counter.most_common(3):
            print(f" - {count}x {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Envia muitas mensagens para o endpoint de chat."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_URL,
        help=f"URL do endpoint (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=15,
        help="Quantidade total de mensagens a serem enviadas.",
    )
    parser.add_argument(
        "--switch-every",
        type=int,
        default=3,
        help="Numero de mensagens antes de gerar um novo UUID.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.0,
        help="Intervalo (em segundos) entre cada requisicao.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Tempo limite individual por requisicao em segundos.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nao exibe o log detalhado de cada requisicao.",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()

    if args.total <= 0:
        raise ValueError("--total deve ser maior que zero")
    if args.switch_every <= 0:
        raise ValueError("--switch-every deve ser maior que zero")

    results = await run_stress_test(
        total_requests=args.total,
        url=args.base_url,
        change_session_every=args.switch_every,
        pause=args.pause,
        timeout=args.timeout,
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

