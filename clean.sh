#!/bin/bash
# Quick cleanup script for PathoGen
# Removes all generated reports, results, and cached files

echo "🧹 Cleaning PathoGen generated files..."
cd "$(dirname "$0")"
python3 cleanup.py
