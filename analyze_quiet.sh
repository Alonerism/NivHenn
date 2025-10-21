#!/bin/bash
# Interactive Property Analyzer Runner (Quiet Mode)
# Suppresses deprecation warnings for cleaner output

export PYTHONWARNINGS="ignore::DeprecationWarning"
.venv/bin/python interactive_analyzer.py "$@"
