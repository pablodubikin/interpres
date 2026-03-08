#!/usr/bin/env python3
"""Send a file attachment to a Discord thread."""
import json
import os
import sys
import requests


def push_file(thread_id: str, file_path: str, message: str = ""):
    """Upload a file to a Discord channel/thread as a message attachment."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    headers = {"Authorization": f"Bot {token}"}

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        files = {"files[0]": (filename, f, _mime_type(filename))}
        data = {"payload_json": json.dumps({"content": message})}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code in (200, 201):
        print(f"File sent to thread {thread_id}: {filename}")
    else:
        print(f"Failed to send file: {response.status_code} - {response.text}", file=sys.stderr)
        sys.exit(1)


def _mime_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp"}.get(ext, "application/octet-stream")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 push_file.py <thread_id> <file_path> [message]", file=sys.stderr)
        sys.exit(1)

    thread_id = sys.argv[1]
    file_path = sys.argv[2]
    message = sys.argv[3] if len(sys.argv) > 3 else ""
    push_file(thread_id, file_path, message)
