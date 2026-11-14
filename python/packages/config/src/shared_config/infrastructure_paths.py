"""Reserved URL paths that product routes must not reuse.

``/livez`` and ``/readyz`` are the kubelet probe contract. ``/metrics`` is the
scrape contract. They are not deployment settings: a ``.env`` typo must not
rename a path kubelet or Prometheus already calls. Each app mounts the probe
routes. ``PrometheusManager`` mounts the scrape route and excludes all three
from default HTTP series.
"""

from typing import Final

LIVEZ_ENDPOINT: Final = "/livez"
READYZ_ENDPOINT: Final = "/readyz"
METRICS_ENDPOINT: Final = "/metrics"
