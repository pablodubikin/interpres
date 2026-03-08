# Interpres

A Discord bot that bridges [Claude Code](https://claude.ai/claude-code) and Discord, letting you interact with an AI coding agent directly from Discord threads. Each thread maintains its own Claude session, preserving context across messages.

## Features

- Send prompts to Claude Code from any Discord thread
- Attach images or files — they're forwarded to Claude as context
- Sessions are persisted per thread — Claude remembers context across messages
- Project-aware: resolves project paths from Discord channel topics
- Admin commands for status, logs, and restart via Discord

## Requirements

- Python 3.8+
- [`claude` CLI](https://claude.ai/claude-code) installed and authenticated
- A Discord bot token

## Setup

**1. Clone and install dependencies:**
```bash
git clone https://github.com/pablodubikin/interpres.git
cd interpres
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create a `.env` file in the project root:**
```
DISCORD_TOKEN=your_discord_bot_token
PROJECTS_BASE_DIR=/home/youruser/projects
DISCORD_GUILD_ID=your_guild_id
```

**3. Run the bot:**
```bash
venv/bin/python3 bot.py
```

## Running as a systemd user service

**Install the service:**
```bash
mkdir -p ~/.config/systemd/user
ln -s ~/projects/interpres/interpres.service ~/.config/systemd/user/interpres.service
systemctl --user daemon-reload
systemctl --user enable --now interpres
```

**If you want the bot to keep running after logout:**
```bash
sudo loginctl enable-linger $USER
```

### Service commands

| Action | Command |
|--------|---------|
| Start | `systemctl --user start interpres` |
| Stop | `systemctl --user stop interpres` |
| Restart | `systemctl --user restart interpres` |
| Status | `systemctl --user status interpres` |
| Enable on boot | `systemctl --user enable interpres` |
| Disable on boot | `systemctl --user disable interpres` |

### Logs

**Follow logs in real time:**
```bash
journalctl --user -u interpres -f
```

**Show last 50 lines:**
```bash
journalctl --user -u interpres -n 50
```

**Show logs since last boot:**
```bash
journalctl --user -u interpres -b
```

## Discord commands

| Command | Description |
|---------|-------------|
| `<any message>` | Send a prompt to Claude Code in the current thread |
| `/projects` | List available projects |
| `/channel <name>` | Create a Discord channel for a project |
| `/metabot status` | Check if the bot process is running |
| `/metabot logs` | View the last 50 lines of `bot.log` |
| `/metabot restart` | Restart the bot process |

## Configuration

| Environment variable | Required | Description |
|---------------------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `PROJECTS_BASE_DIR` | No | Base directory for projects (default: `~/projects`) |
| `DISCORD_GUILD_ID` | No | Guild ID, used by `sync_channels.py` |
| `DISCORD_CATEGORY` | No | Channel category prefix (default: `projects`) |
