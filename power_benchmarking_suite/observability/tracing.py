"""
OpenTelemetry Tracing Configuration

Provides distributed tracing with W3C Trace Context propagation.
"""

from typing import Optional
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    Resource = None
    TraceContextTextMapPropagator = None


def setup_tracing(
    service_name: str = "power-benchmarking-suite",
    enable_console: bool = True,
    sampling_rate: float = 1.0,
) -> Optional[object]:
    """
    Set up OpenTelemetry tracing.

    Args:
        service_name: Service name for traces
        enable_console: Enable console exporter (for development)
        sampling_rate: Sampling rate (0.0 to 1.0)

    Returns:
        TracerProvider if OpenTelemetry is available, None otherwise
    """
    if not OPENTELEMETRY_AVAILABLE:
        return None

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if enable_console:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    return provider


def get_tracer(name: str) -> Optional[object]:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (typically __name__)

    Returns:
        Tracer instance if OpenTelemetry is available, None otherwise
    """
    if not OPENTELEMETRY_AVAILABLE:
        return None

    return trace.get_tracer(name)


@contextmanager
def trace_span(tracer, name: str, attributes: Optional[dict] = None):
    """
    Context manager for creating spans.
    """
    if not tracer:
        yield None
        return

    # start_as_current_span returns a context manager; enter it to get a Span
    from opentelemetry.trace import Status, StatusCode  # type: ignore
    try:
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    try:
                        span.set_attribute(key, value)
                    except Exception:
                        pass
            try:
                yield span
            except Exception as e:
                try:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                except Exception:
                    pass
                raise
    except Exception:
        # If tracing fails, yield None to avoid breaking execution
        yield None
        return

