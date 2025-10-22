
import logging as _logging

# Try to use rich if available; otherwise fall back to stdlib only.
try:  # optional dependency
    from rich.logging import RichHandler as _RichHandler  # type: ignore
    _HAS_RICH = True
except Exception:  # ImportError or missing pygments in rich
    _RichHandler = None  # type: ignore
    _HAS_RICH = False

_LOG_FORMAT = "%(message)s"

def setup_logging(level: str = "INFO") -> None:
    lvl = getattr(_logging, level.upper(), _logging.INFO)
    if _HAS_RICH and _RichHandler is not None:
        _logging.basicConfig(
            level=lvl,
            format=_LOG_FORMAT,
            datefmt="%H:%M:%S",
            handlers=[_RichHandler(rich_tracebacks=True, markup=True)],
        )
    else:
        handler = _logging.StreamHandler()
        formatter = _logging.Formatter(_LOG_FORMAT)
        handler.setFormatter(formatter)
        root = _logging.getLogger()
        root.setLevel(lvl)
        # clear existing handlers to avoid duplicate logs when reloading
        root.handlers = [handler]
