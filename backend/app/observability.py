from __future__ import annotations

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

try:
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
except Exception:  # pragma: no cover
    ConsoleSpanExporter = None  # type: ignore


def setup_tracing(app) -> None:
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return
    resource = Resource.create({"service.name": "opspilot-api"})
    provider = TracerProvider(resource=resource)
    if ConsoleSpanExporter is not None:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


