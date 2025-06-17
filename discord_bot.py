import discord
import os
from dotenv import load_dotenv

from discord.ext import commands
from discord import app_commands
import aiohttp


# Load environment variables from .env file
load_dotenv()
GUILD_ID = discord.Object(id=os.getenv('server_id'))
cortana_api_url = 'https://wolf1997-cortana-api.hf.space'
# cortana_api_url = 'http://localhost:8000'
keys = {
        "google_api_key": os.getenv("google_api_key", ""),
        "tavily_key": os.getenv("tavily_key", ""),
        "pse": os.getenv("pse", ""),
        "openai_api_key": os.getenv("openai_api_key", ""),
        "composio_key": os.getenv("composio_api_key", ""),
        "hf_token": os.getenv("hf_token", "")
    }
class Client(commands.Bot):
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        try:
            
            synced = await self.tree.sync(guild=GUILD_ID)
            print(f'Synced {len(synced)} commands')
        except Exception as e:
            print(f'Error syncing commands: {e}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # If no content and no attachments, ignore
        if not message.content and not message.attachments:
            return
            
        try:
            # Prepare the data payload (like gradio example)
            data = {
                "query": message.content,
                "google_api_key": keys['google_api_key'],
                "tavily_key": keys['tavily_key'],
                "include_audio": 'False'  # Set to 'true' if you want audio responses
            }
            
            # Add optional API keys if provided
            optional_keys = ["pse", "openai_api_key", "composio_key", "hf_token"]
            for key in optional_keys:
                if keys[key]:
                    data[key] = keys[key]
            
            # Prepare files for upload (separate from data, like gradio)
            files_payload = {}
            
            # Handle attachments if present
            if message.attachments:
                attachment = message.attachments[0]  # Handle first attachment
                
                # Download the attachment
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            file_data = await resp.read()
                            
                            # Determine file type based on content type or filename
                            content_type = attachment.content_type or 'application/octet-stream'
                            filename = attachment.filename.lower()
                            
                            if content_type.startswith('image/') or filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                files_payload["image"] = (attachment.filename, file_data, content_type)
                            elif filename.endswith('.ogg') or content_type.startswith('audio/'):
                                files_payload["voice"] = (attachment.filename, file_data, content_type)
                            else:
                                files_payload["document"] = (attachment.filename, file_data, content_type)
            
            # Make request to Cortana API
            chat_url = f"{cortana_api_url}/chat"
            
            # Create FormData for aiohttp (equivalent to requests.post with data and files)
            form_data = aiohttp.FormData()
            
            # Add regular data fields
            for key, value in data.items():
                form_data.add_field(key, value)
            
            # Add file fields if any
            for key, (filename, file_data, content_type) in files_payload.items():
                form_data.add_field(key, file_data, filename=filename, content_type=content_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(chat_url, data=form_data) as resp:
                    if resp.status == 200:
                        response_data = await resp.json()
                        cortana_response = response_data.get('response', 'Sorry, I could not process your request.')
                        
                        # Send response back to Discord
                        await message.channel.send(f'{message.author.mention}, {cortana_response}')
                        
                        # If audio URL is provided, you could send it as well
                        if response_data.get('audio_url'):
                            await message.channel.send(f"Audio response: {response_data['audio_url']}")
                    else:
                        error_text = await resp.text()
                        print(f"API Error: {resp.status} - {error_text}")
                        await message.channel.send(f'{message.author.mention}, Sorry, I encountered an error processing your request.')
                        
        except Exception as e:
            print(f"Error in on_message: {e}")
            await message.channel.send(f'{message.author.mention}, Sorry, I encountered an error: {str(e)}')

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)


@client.tree.command(name='reset_cortana', description='Reset the conversation', guild=GUILD_ID)
async def reset_cortana(interaction: discord.Interaction):
    try:
        # Make request to reset endpoint
        
        reset_url = f"{cortana_api_url}/reset"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(reset_url) as resp:
                if resp.status == 200:
                    await interaction.response.send_message(f'{interaction.user.mention}, Cortana\'s memory has been reset successfully.')
                else:
                    await interaction.response.send_message(f'{interaction.user.mention}, Failed to reset Cortana\'s memory.')
    except Exception as e:
        print(f"Error in reset_cortana: {e}")
        await interaction.response.send_message(f'{interaction.user.mention}, Error resetting Cortana: {str(e)}')

client.run(os.getenv('bot_token'))