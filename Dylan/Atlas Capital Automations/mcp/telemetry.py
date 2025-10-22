"""
Telemetry MCP
-------------

This module provides helper functions for emitting metrics and traces
from MCP components.  It builds upon the Prometheus and OpenTelemetry
instrumentation already configured in the ``app`` package.  These
functions can be called by other MCP modules to record usage
information in a consistent manner.

Functions
~~~~~~~~~

``record_metric(name: str, value: float, labels: dict = None)``
    Increment or observe a Prometheus metric.  If the metric does
    not exist, it will be created as a counter.

``record_trace(name: str, attributes: dict = None)``
    Create an OpenTelemetry span with optional attributes.  Requires
    OpenTelemetry to be initialised via ``app.telemetry.init_tracing``.

These utilities keep the core MCP logic free of monitoring boilerplate.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from prometheus_client import Counter

try:
    from opentelemetry import trace
except ImportError:
    trace = None  # type: ignore


_METRIC_CACHE: Dict[str, Counter] = {}


def record_metric(name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
    """Record a Prometheus metric.

    If the metric does not exist it is created as a counter.  Counters
    can only be incremented, so negative values are ignored.

    Parameters
    ----------
    name : str
        The metric name.  Should be a valid Prometheus identifier.
    value : float, optional
        Amount to increment the counter.  Defaults to 1.0.
    labels : dict, optional
        Optional label key/values.  If provided they will be
        attached to the counter.
    """
    if name not in _METRIC_CACHE:
        _METRIC_CACHE[name] = Counter(name, f"MCP metric {name}", list(labels.keys()) if labels else [])
    counter = _METRIC_CACHE[name]
    if labels:
        counter.labels(**labels).inc(value)
    else:
        counter.inc(value)


def record_trace(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Record an OpenTelemetry span.

    Requires that ``opentelemetry`` is installed and tracing has been
    initialised via :func:`app.telemetry.init_tracing`.  If the
    tracer provider is not available, this function does nothing.

    Parameters
    ----------
    name : str
        Span name.
    attributes : dict, optional
        Attributes to attach to the span.
    """
    if trace is None:
        return
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)