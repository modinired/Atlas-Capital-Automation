"""
OpenTelemetry tracing support for Terry Delmonaco Presents: AI.

This module provides a helper to configure distributed tracing for the FastAPI
application.  When tracing is enabled via the ``ENABLE_TRACES`` environment
variable and an OTLP endpoint is provided via ``OTLP_ENDPOINT``, the service
will export spans to the configured collector.  Spans are tagged with the
service name defined in ``Settings.service_name`` and the service version.

The implementation uses the OpenTelemetry SDK and FastAPI instrumentation.
For more information on the configuration options see the OpenTelemetry
documentation.
"""

from __future__ import annotations

from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.config import settings

_instrumented: bool = False


def init_tracing(app) -> None:
    """Initialize OpenTelemetry tracing for the given FastAPI app.

    If tracing is disabled or no OTLP endpoint is configured, this function
    returns immediately.  Otherwise it sets up a tracer provider with a
    ``BatchSpanProcessor`` that exports spans to the OTLP endpoint and
    instruments the FastAPI application to automatically generate spans for
    incoming requests.

    Args:
        app: The FastAPI application instance to instrument.
    """
    global _instrumented
    # Only instrument once per process
    if _instrumented:
        return
    if not settings.enable_traces:
        return
    if not settings.otlp_endpoint:
        return
    # Configure resource attributes for the service
    resource = Resource.create({
        "service.name": settings.service_name,
        "service.version": settings.service_version,
    })
    # Set up the tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    # Create the OTLP exporter.  We use insecure transport here because the
    # endpoint may be internal; for production deployments configure TLS as
    # appropriate.
    exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    # Instrument FastAPI; this will wrap routes and middleware to emit spans
    FastAPIInstrumentor.instrument_app(app)
    _instrumented = True