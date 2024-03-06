import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_actionrow, create_button, ButtonStyle
from discord_slash.model import ButtonStyle
import json

# Load config from config.json
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)
slash = SlashCommand(bot, sync_commands=True)  # Create a new SlashCommand instance

from discord_slash import ComponentContext

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await update_custom_status()

@slash.slash(
    name="set_status",
    description="Set the bot's custom status.",
    options=[
        create_option(
            name="type",
            description="Type of status (playing, listening, watching, competing).",
            option_type=3,
            required=True
        ),
        create_option(
            name="text",
            description="Text to display as status.",
            option_type=3,
            required=True
        )
    ],
    guild_ids=[]
)
async def set_status(ctx: SlashContext, type: str, text: str):
    config = load_config()
    if ctx.author.roles and any(role.id in config.get('allowed_roles', []) for role in ctx.author.roles):
        config['custom_status'] = {'type': type.lower(), 'text': text}
        with open('config.json', 'w') as f:
            json.dump(config, f)
        await update_custom_status()
        await ctx.send(f"Custom status updated to {type.lower()} '{text}'.")
    else:
        await ctx.send("You do not have permission to use this command.")

@slash.slash(
    name="send_dm",
    description="Sends a custom embedded message to a user or all users in the server.",
    options=[
        create_option(
            name="message",
            description="The message you want to send.",
            option_type=3,
            required=True
        ),
        create_option(
            name="user",
            description="The user you want to send the message to.",
            option_type=6,
            required=False
        ),
        create_option(
            name="dm_all",
            description="Send message to all users in the server.",
            option_type=5,
            required=False
        )
    ],
    guild_ids=[]
)
async def send_dm(ctx: SlashContext, message: str, user: discord.User = None, dm_all: bool = False):
    config = load_config()
    if ctx.author.roles and any(role.id in config.get('allowed_roles', []) for role in ctx.author.roles):
        embed_settings = config['embed_settings']
        embed = discord.Embed(
            title=embed_settings['title'],
            description=message,
            color=getattr(discord.Color, embed_settings['color'].lower())(),
        )
        embed.set_footer(text=embed_settings['footer_text'])
        embed.set_thumbnail(url=embed_settings['thumbnail_url'])

        if config.get('debug_mode', False):
            print(f"Debug Mode: Sending message - {message}")

        if dm_all:
            members = ctx.guild.members
            await ctx.send(f"Sending message to {len(members)} members (excluding bots)...")
            for member in members:
                if not member.bot:  # Skip bots
                    try:
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        continue
            await ctx.send("Message sent to all members (excluding bots).")
        else:
            if user is None:
                await ctx.send("You need to specify a user or enable the 'dm_all' option to send to all users.")
            else:
                await user.send(embed=embed)
                await ctx.send(f"Sent a custom embedded message to {user.name}.")
    else:
        await ctx.send("You do not have permission to use this command.")

@slash.slash(
    name="refresh_config",
    description="Refresh the bot's configuration.",
    guild_ids=[]
)
async def refresh_config(ctx: SlashContext):
    config = load_config()
    if ctx.author.roles and any(role.id in config.get('allowed_roles', []) for role in ctx.author.roles):
        # Logic to refresh the configuration
        await ctx.send("Bot configuration refreshed.")
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.event
async def on_component(ctx: ComponentContext):
    await ctx.defer()
    await ctx.send(content="Button clicked!", ephemeral=True)

async def update_custom_status():
    config = load_config()
    custom_status = config.get('custom_status', {})
    status_type = getattr(discord.ActivityType, custom_status.get('type', 'playing').upper(), discord.ActivityType.playing)
    await bot.change_presence(activity=discord.Activity(type=status_type, name=custom_status.get('text', '')))

@slash.slash(
    name="rich_presence",
    description="Set the bot's rich presence status.",
    guild_ids=[]
)
async def rich_presence(ctx: SlashContext):
    config = load_config()
    button1 = create_button(style=ButtonStyle.URL, label=config['button1_label'], url=config['button1_url'])
    button2 = create_button(style=ButtonStyle.URL, label=config['button2_label'], url=config['button2_url'])
    action_row = create_actionrow(button1, button2)
    await ctx.send("Custom Rich Presence", components=[action_row])

bot.run(load_config()['bot_token'])
