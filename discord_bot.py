import discord
import os
from dotenv import load_dotenv
import requests
from discord.ext import commands
from discord import app_commands

# Load environment variables from .env file
load_dotenv()
GUILD_ID = discord.Object(id=os.getenv('server_id'))
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
        await message.channel.send(f'Hello {message.author.mention}, I am Cortana, your personal assistant\
                                   . you said {message.content} with the attached file {message.attachments}')

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)


@client.tree.command(name='reset_cortana', description='Reset the conversation', guild=GUILD_ID)
async def reset_cortana(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hello {interaction.user.mention}, I am Cortana, your personal assistant.')

client.run(os.getenv('bot_token'))