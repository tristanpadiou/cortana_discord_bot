import discord
import os
from dotenv import load_dotenv
import asyncio
import io
import tempfile
import subprocess
import platform
from discord.ext import commands
from discord import app_commands
import aiohttp
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def setup_ffmpeg():
    """Ensure FFmpeg is available"""
    try:
        # Try to run ffmpeg to see if it's available
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found in PATH")
        
        if platform.system() == "Windows":
            # Check common WinGet installation location for local development
            import glob
            winget_pattern = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*")
            winget_dirs = glob.glob(winget_pattern)
            
            for winget_dir in winget_dirs:
                ffmpeg_pattern = os.path.join(winget_dir, "*", "bin", "ffmpeg.exe")
                ffmpeg_paths = glob.glob(ffmpeg_pattern)
                if ffmpeg_paths:
                    ffmpeg_dir = os.path.dirname(ffmpeg_paths[0])
                    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + ffmpeg_dir
                    print(f"✅ Added FFmpeg to PATH: {ffmpeg_dir}")
                    return True
            
            print("⚠️  FFmpeg not found. Voice playback may not work.")
            print("Install FFmpeg with: winget install 'FFmpeg (Essentials Build)'")
        else:
            # On Linux/Docker environments
            print("⚠️  FFmpeg not found. Install with: apt-get install ffmpeg")
        
        return False

# Load environment variables from .env file
load_dotenv()

# Setup FFmpeg
setup_ffmpeg()

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recording = False
        
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            print(f'Synced {len(synced)} commands')
        except Exception as e:
            print(f'Error syncing commands: {e}')



    async def play_audio_response(self, guild, audio_url):
        """Play audio response in voice channel"""
        try:
            voice_client = guild.voice_client
            if voice_client and voice_client.is_connected():
                # Download audio file
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as resp:
                        if resp.status == 200:
                            audio_data = await resp.read()
                            
                            # Create temporary file for audio
                            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                                temp_file.write(audio_data)
                                temp_file_path = temp_file.name
                            
                            # Play the audio
                            voice_client.play(discord.FFmpegPCMAudio(temp_file_path))
                            
                            # Wait for playback to finish
                            while voice_client.is_playing():
                                await asyncio.sleep(0.1)
                            
                            # Clean up
                            os.unlink(temp_file_path)
        except Exception as e:
            print(f"Error playing audio response: {e}")

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
            is_voice_message = False
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
                            elif (filename.endswith(('.ogg', '.mp3', '.wav', '.m4a', '.aac', '.flac')) or 
                                  content_type.startswith('audio/')):
                                files_payload["voice"] = (attachment.filename, file_data, content_type)
                                is_voice_message = True
                                # For voice messages, request audio response
                                data["include_audio"] = 'True'
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
                        
                        # If audio URL is provided and this was a voice message, play it in voice channel
                        if response_data.get('audio_url'):
                            if is_voice_message and message.guild.voice_client:
                                await client.play_audio_response(message.guild, response_data['audio_url'])
                                await message.channel.send("🔊 Playing audio response in voice channel!")
                            else:
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

# Simple HTTP handler for Hugging Face spaces
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            status = "✅ Connected" if client.is_ready() else "⚠️ Connecting..."
            self.wfile.write(f"""
            <html>
                <head><title>Cortana Discord Bot</title></head>
                <body>
                    <h1>Cortana Discord Bot Status</h1>
                    <p>Status: {status}</p>
                    <p>Bot User: {client.user if client.user else 'Not logged in yet'}</p>
                    <p>Guilds: {len(client.guilds) if client.is_ready() else 'N/A'}</p>
                </body>
            </html>
            """.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_http_server():
    """Start a simple HTTP server for Hugging Face spaces"""
    port = int(os.environ.get('PORT', 7860))  # HF spaces typically use port 7860
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 HTTP server starting on port {port}")
    server.serve_forever()

# Voice Commands
@client.tree.command(name='join_voice', description='Join your voice channel', guild=GUILD_ID)
async def join_voice(interaction: discord.Interaction):
    try:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(channel)
            else:
                await channel.connect()
            await interaction.response.send_message(f'Joined {channel.name}!')
        else:
            await interaction.response.send_message('You need to be in a voice channel first!')
    except Exception as e:
        print(f"Error joining voice: {e}")
        await interaction.response.send_message(f'Error joining voice channel: {str(e)}')

@client.tree.command(name='leave_voice', description='Leave the voice channel', guild=GUILD_ID)
async def leave_voice(interaction: discord.Interaction):
    try:
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message('Left the voice channel!')
        else:
            await interaction.response.send_message('Not connected to a voice channel!')
    except Exception as e:
        print(f"Error leaving voice: {e}")
        await interaction.response.send_message(f'Error leaving voice channel: {str(e)}')

@client.tree.command(name='start_listening', description='Start listening for voice commands (push-to-talk alternative)', guild=GUILD_ID)
async def start_listening(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message('Bot is not connected to a voice channel! Use /join_voice first.')
            return
        
        if client.recording:
            await interaction.response.send_message('Already listening for voice commands!')
            return
        
        await interaction.response.send_message('🎤 **Voice Command Mode Active!**\n\n'
                                              '**Instructions:**\n'
                                              '1. Record your voice message using Discord\'s voice recording feature\n'
                                              '2. Send the audio file as an attachment in this chat\n'
                                              '3. I\'ll process it and respond with both text and audio!\n\n'
                                              '**Alternative:** Upload any audio file (.mp3, .wav, .ogg) and I\'ll process it.')
        
    except Exception as e:
        print(f"Error in start_listening: {e}")
        await interaction.response.send_message(f'Error starting voice listening: {str(e)}')

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

# Start HTTP server in a separate thread for Hugging Face spaces
http_thread = threading.Thread(target=start_http_server, daemon=True)
http_thread.start()

# Start the Discord bot
print("🤖 Starting Cortana Discord Bot...")
client.run(os.getenv('bot_token'))