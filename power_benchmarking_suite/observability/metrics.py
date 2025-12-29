"""
Metrics Collection

Provides Prometheus-compatible metrics collection.
"""

from typing import Optional, Dict, Any
from collections import defaultdict

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None
    Histogram = None
    Gauge = None
    start_http_server = None


class MetricsCollector:
    """Metrics collector for power benchmarking suite."""

    def __init__(self):
        self.counters: Dict[str, Any] = {}
        self.histograms: Dict[str, Any] = {}
        self.gauges: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self):
        """Initialize metrics if Prometheus is available."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Power consumption metrics
        self.gauges["ane_power_mw"] = Gauge(
            "ane_power_milliwatts",
            "Current ANE (Neural Engine) power consumption in milliwatts",
            ["component"],
        )
        self.gauges["cpu_power_mw"] = Gauge(
            "cpu_power_milliwatts", "Current CPU power consumption in milliwatts", ["component"]
        )
        self.gauges["gpu_power_mw"] = Gauge(
            "gpu_power_milliwatts", "Current GPU power consumption in milliwatts", ["component"]
        )

        # Inference metrics
        self.counters["inference_total"] = Counter(
            "inference_total", "Total number of inferences", ["model", "compute_unit"]
        )
        self.histograms["inference_duration_seconds"] = Histogram(
            "inference_duration_seconds", "Inference duration in seconds", ["model", "compute_unit"]
        )

        # Thermal metrics
        self.gauges["thermal_throttle_events"] = Gauge(
            "thermal_throttle_events_total", "Number of thermal throttling events", ["component"]
        )

        # Error metrics
        self.counters["errors_total"] = Counter(
            "errors_total", "Total number of errors", ["error_type", "component"]
        )

        self._initialized = True

    def record_power(self, component: str, power_mw: float):
        """Record power consumption."""
        if not self._initialized:
            return

        if component == "ane":
            self.gauges["ane_power_mw"].labels(component=component).set(power_mw)
        elif component == "cpu":
            self.gauges["cpu_power_mw"].labels(component=component).set(power_mw)
        elif component == "gpu":
            self.gauges["gpu_power_mw"].labels(component=component).set(power_mw)

    def record_inference(self, model: str, compute_unit: str, duration: float):
        """Record inference metrics."""
        if not self._initialized:
            return

        self.counters["inference_total"].labels(model=model, compute_unit=compute_unit).inc()

        self.histograms["inference_duration_seconds"].labels(
            model=model, compute_unit=compute_unit
        ).observe(duration)

    def record_thermal_throttle(self, component: str):
        """Record thermal throttling event."""
        if not self._initialized:
            return

        self.gauges["thermal_throttle_events"].labels(component=component).inc()

    def record_error(self, error_type: str, component: str):
        """Record error."""
        if not self._initialized:
            return

        self.counters["errors_total"].labels(error_type=error_type, component=component).inc()


_metrics_collector: Optional[MetricsCollector] = None


def setup_metrics(port: int = 8000) -> Optional[MetricsCollector]:
    """
    Set up metrics collection.

    Args:
        port: Port for metrics HTTP server

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector

    if not PROMETHEUS_AVAILABLE:
        return None

    _metrics_collector = MetricsCollector()
    _metrics_collector.initialize()

    # Start metrics HTTP server
    try:
        start_http_server(port)
    except Exception:
        pass  # Port might be in use, continue anyway

    return _metrics_collector


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get the global metrics collector instance."""
    return _metrics_collector

