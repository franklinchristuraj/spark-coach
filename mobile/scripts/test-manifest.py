#!/usr/bin/env python3
"""Verify manifest.json has required PWA fields."""
import json
import sys

with open("public/manifest.json") as f:
    m = json.load(f)

errors = []
for field in ["name", "short_name", "display", "start_url", "icons", "theme_color", "background_color"]:
    if field not in m:
        errors.append(f"Missing required field: {field}")

if m.get("display") not in ["standalone", "fullscreen", "minimal-ui"]:
    errors.append(f"Invalid display value: {m.get('display')}")

icons = m.get("icons", [])
sizes = {i.get("sizes") for i in icons}
for required_size in ["192x192", "512x512"]:
    if required_size not in sizes:
        errors.append(f"Missing icon size: {required_size}")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)

print("PASS: manifest.json is valid")
