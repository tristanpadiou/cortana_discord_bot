# Discord Bot Bearer Token Setup

Your Cortana Discord Bot has been updated to use the new bearer token authentication system.

## What Changed

- **Before**: The bot used individual API keys (`google_api_key`, `tavily_key`, etc.) passed with each request
- **After**: The bot now uses a single bearer token to authenticate with the Cortana API

## Required Environment Variables

Create a `.env` file in the `cortana_discord_bot` directory with:

```bash
# Discord Bot Configuration
DISCORD_TOKEN=your-discord-bot-token-here
DISCORD_SERVER_ID=your-server-id-here

# Cortana API Configuration  
CORTANA_API_URL=http://localhost:8000
BEARER_TOKEN=your-bearer-token-here

# Optional: If you want to override the default port for HTTP health check
# PORT=7860
```

## Environment Variables Explained

### Required Variables:
- `DISCORD_TOKEN`: Your Discord bot token from the Discord Developer Portal
- `BEARER_TOKEN`: The bearer token for authenticating with your Cortana API (must match one configured in the Cortana API)

### Optional Variables:
- `DISCORD_SERVER_ID`: Your Discord server ID for slash commands (if not set, commands will be global)
- `CORTANA_API_URL`: URL of your Cortana API (defaults to `http://cortana-api:8000`)
- `PORT`: Port for HTTP health check server (defaults to 7860)

## Bearer Token Setup

The `BEARER_TOKEN` must be one of the valid tokens configured in your Cortana API. You can:

1. **Use the same token** as configured in your Cortana API's `config.yaml` or environment variables
2. **Generate a new secure token**:
   ```python
   import secrets
   token = secrets.token_urlsafe(32)
   print(f"Bearer token: {token}")
   ```
3. **Add the token to your Cortana API configuration**

## Migration Steps

1. **Stop the old Discord bot** if it's running
2. **Update environment variables** in your `.env` file:
   - Remove old API key variables: `google_api_key`, `tavily_key`, `openai_api_key`, `hf_token`, etc.
   - Add `BEARER_TOKEN` with a valid token from your Cortana API
3. **Ensure your Cortana API is running** with bearer token authentication enabled
4. **Start the updated Discord bot**

## Features Still Supported

All existing Discord bot features continue to work:
- ✅ Text messages and responses
- ✅ Image uploads and analysis
- ✅ Voice message processing
- ✅ Document uploads
- ✅ Audio responses in voice channels
- ✅ Slash commands (`/join_voice`, `/leave_voice`, `/reset_cortana`, etc.)

## Troubleshooting

### "BEARER_TOKEN environment variable not set!" Error
- Make sure you have `BEARER_TOKEN=your-token-here` in your `.env` file
- Verify the `.env` file is in the same directory as `discord_bot.py`
- Check that your token doesn't have extra spaces or quotes

### "Invalid authentication token" API Error
- Verify your bearer token matches one configured in the Cortana API
- Check that your Cortana API is running and accessible at `CORTANA_API_URL`
- Ensure the Cortana API has bearer token authentication properly configured

### Bot Commands Not Working
- Make sure your Discord bot has the necessary permissions in your server
- If using `DISCORD_SERVER_ID`, verify it's the correct server ID
- Check the bot logs for any error messages

## Testing the Setup

1. **Start your Cortana API** with bearer token authentication
2. **Start the Discord bot**: `python discord_bot.py`
3. **Test basic functionality**:
   - Send a text message to the bot
   - Try uploading an image
   - Use the `/reset_cortana` slash command
4. **Check for errors** in both the Discord bot and Cortana API logs

The bot will now authenticate securely with your Cortana API using bearer tokens!
