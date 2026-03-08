#!/usr/bin/env python3
"""Capture a specific window by name/class keyword and save as PNG.

Usage:
    python3 window_screenshot.py <search_term> [output_path]

Examples:
    python3 window_screenshot.py chrome
    python3 window_screenshot.py terminal /tmp/term.png
    python3 window_screenshot.py sublime
"""
import os
import re
import subprocess
import sys
import tempfile


def list_windows():
    """Return list of window dicts from xwininfo -root -tree."""
    result = subprocess.run(
        ["xwininfo", "-root", "-tree"],
        capture_output=True, text=True,
        env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":1")},
    )
    windows = []
    # Line format: 0x<id> "title": ("class" "Class")  WxH+X+Y  +AbsX+AbsY
    pattern = re.compile(
        r'(0x[0-9a-f]+)\s+"([^"]*)"\s*:\s*\("([^"]*)"[^)]*\)\s+(\d+)x(\d+)\+(-?\d+)\+(-?\d+)'
    )
    for line in result.stdout.splitlines():
        m = pattern.search(line)
        if m:
            win_id, title, cls, w, h, x, y = m.groups()
            windows.append({
                "id": win_id,
                "title": title,
                "class": cls,
                "w": int(w), "h": int(h),
                "x": int(x), "y": int(y),
            })
    return windows


def find_window(search_term):
    """Find the best matching window for the search term."""
    windows = list_windows()
    term = search_term.lower()
    matches = [
        w for w in windows
        if (term in w["title"].lower() or term in w["class"].lower())
        and w["w"] > 50 and w["h"] > 50
    ]
    if not matches:
        return None
    # Pick the largest matching window (most likely the real app window)
    return max(matches, key=lambda w: w["w"] * w["h"])


def capture_window(search_term, output_path):
    """Take a full screenshot then crop to the matched window bounds."""
    window = find_window(search_term)
    if not window:
        print(f"No window found matching: {search_term!r}", file=sys.stderr)
        print("Available windows:", file=sys.stderr)
        for w in list_windows():
            if w["w"] > 50 and w["h"] > 50:
                print(f"  [{w['class']}] {w['title']!r} {w['w']}x{w['h']}", file=sys.stderr)
        sys.exit(1)

    print(f"Matched: {window['title']!r} [{window['class']}] "
          f"at ({window['x']},{window['y']}) size {window['w']}x{window['h']}")

    # Take full screenshot to a temp file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["gnome-screenshot", "-f", tmp_path],
            env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":1")},
            check=True,
        )

        from PIL import Image
        img = Image.open(tmp_path)
        img_w, img_h = img.size

        # Clamp crop region to actual image bounds
        x = max(0, window["x"])
        y = max(0, window["y"])
        w = min(window["w"], img_w - x)
        h = min(window["h"], img_h - y)

        cropped = img.crop((x, y, x + w, y + h))
        cropped.save(output_path)
        print(f"Saved cropped window to {output_path}")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: window_screenshot.py <search_term> [output_path]", file=sys.stderr)
        sys.exit(1)

    term = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/claude_window_screenshot.png"
    capture_window(term, out)
