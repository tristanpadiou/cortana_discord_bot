# Cortana Discord Bot

A basic Discord bot for sending messages to specific servers and channels.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a Discord Bot:
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to the "Bot" section
   - Create a bot and copy the token

3. Configure the bot:
   - Create a `.env` file in the root directory
   - Add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

4. Invite the bot to your server:
   - Go to the "OAuth2" > "URL Generator" section
   - Select "bot" scope
   - Select "Send Messages" permission
   - Copy and visit the generated URL to invite the bot

## Docker Setup (Alternative)

You can also run the Discord bot using Docker, which provides a consistent environment and easier deployment.

### Prerequisites

- Docker installed on your system
- Discord bot token (follow steps 2-4 from the Setup section above)

### Building and Running with Docker

1. Build the Docker image:
```bash
docker build -t cortana-discord-bot .
```

2. Run the container with your Discord token:
```bash
docker run -e DISCORD_TOKEN=your_bot_token_here cortana-discord-bot
```

3. For production deployment, you can also run in detached mode:
```bash
docker run -d --name cortana-bot -e DISCORD_TOKEN=your_bot_token_here cortana-discord-bot
```

### Using Docker Compose (Recommended)

Create a `docker-compose.yml` file:
```yaml
version: '3.8'
services:
  cortana-bot:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
    restart: unless-stopped
```

Then create a `.env` file with your token:
```
DISCORD_TOKEN=your_bot_token_here
```

Run with Docker Compose:
```bash
docker-compose up -d
```

### Docker Commands

- **View logs**: `docker logs cortana-bot`
- **Stop the bot**: `docker stop cortana-bot`
- **Remove container**: `docker rm cortana-bot`
- **Rebuild and restart**: `docker-compose up -d --build`

## Usage

### Basic Message Sending

```python
import asyncio
from discord_bot import send_discord_message

# Send a message to a specific channel
channel_id = 123456789012345678  # Replace with actual channel ID
message = "Hello from Cortana!"

asyncio.run(send_discord_message(channel_id, message))
```

### Using the DiscordBot Class

```python
import asyncio
from discord_bot import DiscordBot

async def main():
    bot = DiscordBot("your_bot_token")
    
    # Send to a specific channel by ID
    await bot.send_message_to_channel(123456789012345678, "Hello!")
    
    # Send to a channel by server ID and channel name
    await bot.send_message_to_server(123456789012345678, "general", "Hello!")

asyncio.run(main())
```

## Features

- Send messages to Discord channels by ID
- Send messages to Discord channels by server ID and channel name
- Error handling for permissions and network issues
- Environment variable support for secure token storage