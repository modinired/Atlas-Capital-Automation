
# Ensure logging setup does not require rich/pygments to be installed.
from cesar_src import logging as clog

def test_setup_logging_fallback():
    # Should not raise even if rich is unavailable in environment
    clog.setup_logging("INFO")
