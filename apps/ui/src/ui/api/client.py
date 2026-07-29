from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
from httpx_sse import connect_sse

from ui.api.models import (
    AgentProgressEvent,
    AnalyzeResponse,
    AnalyzeResult,
    normalize_result_payload,
)
from ui.config import settings


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def submit_analysis(
    *,
    token: str,
    user_name: str,
    phone: str,
    email: str,
    description: str,
    cv_name: str,
    cv_bytes: bytes,
) -> AnalyzeResponse:
    url = f"{settings.api_base_url.rstrip('/')}/analyze"
    files = {"cv": (cv_name, cv_bytes)}
    data = {
        "user_name": user_name,
        "phone": phone,
        "email": email,
        "description": description,
    }
    with httpx.Client(timeout=60.0) as client:
        res = client.post(
            url,
            data=data,
            files=files,
            headers=_auth_headers(token),
        )
    if res.status_code >= 400:
        raise ApiError(
            f"Analysis submission failed: {res.status_code} {res.text}",
            status_code=res.status_code,
        )
    return AnalyzeResponse.model_validate(res.json())


def subscribe_to_analysis(
    analysis_id: str,
    token: str,
    *,
    on_event: Callable[[AgentProgressEvent], None] | None = None,
) -> Iterator[AgentProgressEvent]:
    url = f"{settings.api_base_url.rstrip('/')}/analyze/{analysis_id}/events"
    with httpx.Client(timeout=None) as client, connect_sse(
        client,
        "GET",
        url,
        headers=_auth_headers(token),
    ) as event_source:
        for sse in event_source.iter_sse():
            if not sse.data:
                continue
            try:
                raw: dict[str, Any] = json.loads(sse.data)
                event = AgentProgressEvent.model_validate(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            if on_event is not None:
                on_event(event)
            yield event


def is_final_event(event: AgentProgressEvent) -> bool:
    if event.node != "result" or event.status != "completed":
        return False
    if not event.payload or not isinstance(event.payload, dict):
        return False
    payload = event.payload
    has_score = "compatibility_score" in payload
    has_roadmap = "personalized_roadmap" in payload
    has_level = "level_resume" in payload or "level_estimate" in payload
    return has_score and has_roadmap and has_level


def extract_result(event: AgentProgressEvent) -> AnalyzeResult | None:
    if not is_final_event(event) or event.payload is None:
        return None
    return normalize_result_payload(event.payload)


def fetch_pdf(analysis_id: str, token: str) -> bytes:
    """Fetch analysis PDF from API.

    Raises:
        ApiError: On API failure, unauthorized access, or incomplete analysis.
    """
    url = f"{settings.api_base_url.rstrip('/')}/analyze/{analysis_id}/pdf"
    headers = _auth_headers(token)

    try:
        response = httpx.get(url, headers=headers, timeout=30.0)
    except httpx.TimeoutException as exc:
        raise ApiError("Tempo esgotado ao gerar PDF") from exc
    except httpx.RequestError as exc:
        raise ApiError(f"Erro de conexão: {exc}") from exc

    if response.status_code == 200:
        return response.content
    if response.status_code == 404:
        raise ApiError("Análise não encontrada")
    if response.status_code == 403:
        raise ApiError("Acesso negado")
    if response.status_code == 400:
        raise ApiError("Análise ainda em andamento")
    raise ApiError(f"Erro ao gerar PDF: {response.text}")


def read_upload_bytes(uploaded_file: Any) -> tuple[str, bytes]:
    name = getattr(uploaded_file, "name", None) or "cv.bin"
    data = uploaded_file.getvalue()
    if isinstance(data, str):
        data = data.encode("utf-8")
    return Path(name).name, data
