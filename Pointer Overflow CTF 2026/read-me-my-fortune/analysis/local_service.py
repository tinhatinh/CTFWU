#!/usr/bin/env python3
"""Run files/service.py unmodified on a host without SIGALRM (Windows).

Only the alarm is stubbed out; every code path the exploit touches
(token check, template.format, FLAG global) is the real one.
"""
import os
import runpy
import signal
import sys

if not hasattr(signal, "SIGALRM"):
    signal.SIGALRM = signal.SIGABRT          # type: ignore[attr-defined]

    def _alarm(_secs):                        # no-op
        return 0

    signal.alarm = _alarm                     # type: ignore[attr-defined]

os.environ.setdefault("POCTF_DEV_MODE", "1")
here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, "..", "files", "service.py")
sys.argv = [target]
runpy.run_path(target, run_name="__main__")
