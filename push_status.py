#!/usr/bin/env python3
"""Push status updates to Discord from CLAUDE_STATUS.txt"""
import os
import sys
import requests

def push_status(thread_id: str, status_file: str = "CLAUDE_STATUS.txt"):
    """Read status file and push content to Discord thread."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(status_file):
        print(f"Error: {status_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(status_file, "r") as f:
        content = f.read().strip()

    if not content:
        print("Status file is empty, skipping", file=sys.stderr)
        sys.exit(0)

    # Truncate if too long for Discord
    if len(content) > 1900:
        content = content[:1900] + "..."

    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }
    payload = {"content": f"📋 **Status update:**\n{content}"}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Status pushed to thread {thread_id}")
    else:
        print(f"Failed to push status: {response.status_code} - {response.text}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python push_status.py <thread_id> [status_file]", file=sys.stderr)
        sys.exit(1)

    thread_id = sys.argv[1]
    status_file = sys.argv[2] if len(sys.argv) > 2 else "CLAUDE_STATUS.txt"
    push_status(thread_id, status_file)
