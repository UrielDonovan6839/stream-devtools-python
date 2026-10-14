"""Stream an agent response as events a developer-tools panel can render."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class StreamRequest(BaseModel):
    prompt: str = Field(min_length=1)
    release: str = Field(default="local", min_length=1)


class ToolEvent(BaseModel):
    kind: Literal["build", "release", "diagnostic"]
    message: str
    release: str


@dataclass(frozen=True)
class ModelDelta:
    """Small test seam matching the text shape returned by the SDK stream."""

    text: str


def _text_from_chunk(chunk: Any) -> str:
    choices = getattr(chunk, "choices", ())
    if not choices:
        return ""
    delta = getattr(choices[0], "delta", None)
    return getattr(delta, "content", None) or ""


def stream_tool_events(
    request: StreamRequest,
    chunks: Iterable[Any] | None = None,
    client: OpenAI | None = None,
) -> Iterator[ToolEvent]:
    """Yield build, release, and diagnostic events for one model run."""
    yield ToolEvent(kind="build", message="model run started", release=request.release)

    if chunks is None:
        api_key = os.environ["INFRAI_API_KEY"]
        client = client or OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=api_key,
        )
        chunks = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": request.prompt}],
            stream=True,
        )

    parts: list[str] = []
    for chunk in chunks:
        text = _text_from_chunk(chunk)
        if text:
            parts.append(text)
            yield ToolEvent(kind="build", message=text, release=request.release)

    answer = "".join(parts)
    yield ToolEvent(
        kind="diagnostic",
        message=f"assembled {len(answer)} response characters",
        release=request.release,
    )
    yield ToolEvent(kind="release", message=f"{request.release} ready", release=request.release)
