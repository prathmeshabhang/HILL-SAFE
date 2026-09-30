"""
backend/app/core/metrics.py
===========================
Lightweight, thread-safe Prometheus-compatible metrics registry and exposition formatter.
Complies with Prometheus text exposition format (text/plain; version=0.0.4).
"""

from __future__ import annotations

import datetime
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class MetricRegistry:
    """Thread-safe collector for counters, gauges, and timers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
        self._gauges: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
        self._help: Dict[str, str] = {}
        self._start_time: float = time.time()

        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        self.define_help("floody_uptime_seconds", "Total uptime of the Floody Shield service in seconds.")
        self.define_help("floody_http_requests_total", "Total HTTP requests processed by endpoint and status.")
        self.define_help("floody_telemetry_packets_total", "Total telemetry packets processed by ingestion status.")
        self.define_help("floody_model_inferences_total", "Total model inferences executed by model identifier.")
        self.define_help("floody_alerts_total", "Total alerts processed by lifecycle state.")
        self.define_help("floody_jobs_total", "Total background jobs executed by status.")
        self.define_help("floody_active_stations", "Current number of registered active ground stations.")
        self.define_help("floody_active_devices", "Current number of registered active sensor devices.")
        self.define_help("floody_current_risk_index", "Current integrated multi-hazard risk index (0.0 - 1.0).")

    def define_help(self, name: str, help_text: str) -> None:
        with self._lock:
            self._help[name] = help_text

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            key = (name, label_key)
            self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            key = (name, label_key)
            self._gauges[key] = float(value)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            return self._counters.get((name, label_key), 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            return self._gauges.get((name, label_key), 0.0)

    def _format_labels(self, label_tuple: Tuple[Tuple[str, str], ...]) -> str:
        if not label_tuple:
            return ""
        items = [f'{k}="{v}"' for k, v in label_tuple]
        return "{" + ",".join(items) + "}"

    def export_text(self) -> str:
        """Renders all metrics in Prometheus text exposition format."""
        with self._lock:
            uptime = time.time() - self._start_time
            self._gauges[("floody_uptime_seconds", ())] = uptime

            lines: List[str] = []

            # Group counters by name
            counter_names = sorted(list({name for name, _ in self._counters.keys()}))
            for c_name in counter_names:
                help_str = self._help.get(c_name, f"Metric {c_name}")
                lines.append(f"# HELP {c_name} {help_str}")
                lines.append(f"# TYPE {c_name} counter")
                for (name, labels), val in sorted(self._counters.items()):
                    if name == c_name:
                        lbl_str = self._format_labels(labels)
                        lines.append(f"{name}{lbl_str} {val}")

            # Group gauges by name
            gauge_names = sorted(list({name for name, _ in self._gauges.keys()}))
            for g_name in gauge_names:
                help_str = self._help.get(g_name, f"Metric {g_name}")
                lines.append(f"# HELP {g_name} {help_str}")
                lines.append(f"# TYPE {g_name} gauge")
                for (name, labels), val in sorted(self._gauges.items()):
                    if name == g_name:
                        lbl_str = self._format_labels(labels)
                        lines.append(f"{name}{lbl_str} {val}")

            return "\n".join(lines) + "\n"


# Global singleton
metrics = MetricRegistry()
