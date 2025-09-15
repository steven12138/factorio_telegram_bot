# Factorio Telegram Bot

Simple Telegram bot for starting and managing a Factorio dedicated server.

## Usage

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create `config.yaml` based on `config-template.yaml` and fill in your admin
   user IDs and a password.

3. Place your Factorio server files inside the `server/` directory.

4. Run the bot:

   ```bash
   python main.py
   ```

The bot listens for commands in Telegram to control the game server.

### CLI usage

You can also launch the server directly for manual control:

```bash
python server_cli.py
```

Type Factorio console commands and they will be sent to the running server.
