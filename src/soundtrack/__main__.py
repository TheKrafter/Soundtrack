# 
# Soundtrack 
# Copyright (c) 2023 Krafter Developer
# 
from logging42 import logger

import os
import sys
import yaml
import uuid
import pkg_resources
from typing import Optional

from xdg import BaseDirectory
import nextcord
from nextcord.ext import commands

from .internal.util import auto_configure, get_invite_url
from .internal import messages


# CLI
if '--help' in sys.argv or '-h' in sys.argv:
    page = [
        'Usage: python3 -m soundtrack [--reconfigure]',
        'Options:',
        '-h, --help     : Shows this help menu',
        '-v, --version  : Displays current installed version',
        '-i, --invite   : Generate the URL for Inviting the bot (Use `-i` for just the URL)',
        '-c, --config   : Fetch the path of the Configuration File',
        '--reconfigure  : Re-run interactive configuration',
        ' ',
        'Non-Zero Exit Codes:',
        '0  : Success',
        '1  : Unknown Error',
        '10 : Config or API Error',
        '20 : Config Error',
        '69 : Nice.'
    ]
    for i in page:
        print(i)
    sys.exit(0)
elif '--version' in sys.argv or '-v' in sys.argv:
    page = [
        f'🎜 Soundtrack v{pkg_resources.get_distribution(__package__).version}',
        'Copyright (c) 2023 Krafter Developer, et al.',
        'Licensed under the MIT License. https://mit-license.org/',
        'Source on GitHub: https://github.com/TheKrafter/Soundtrack'
    ]
    for i in page:
        print(i)
    sys.exit(0)
elif '--invite' in sys.argv or '-i' in sys.argv:
    path = os.path.join(BaseDirectory.xdg_config_home, 'soundtrack', 'config.yml')
    if os.path.exists(path):
        with open(path, "r") as file:
            cfg = yaml.full_load(file)
        if '-i' in sys.argv:
            print(get_invite_url(cfg["client_id"]))
        else:
            page = [
                "🎜 Soundtrack",
                "Invite to your Guild with the following URL:",
                f"    {get_invite_url(cfg["client_id"])}",
            ]
            for i in page:
                print(i)
        sys.exit(0)
    else:
        page = [
            "Bot is not configured!",
            " Please run configuration first."
        ]
        for i in page:
            print(i)
        sys.exit(20)
elif '--configure' in sys.argv or '-c' in sys.argv:
    print(os.path.join(BaseDirectory.xdg_config_home, 'soundtrack', 'config.yml'))
    sys.exit(0)

logger.debug('Starting...')

# Bot Definition
intents = nextcord.Intents.default()
intents.guilds = True
bot = commands.Bot(intents=intents)

# Load Config
config = None
config_dir = os.path.join(BaseDirectory.xdg_config_home, 'soundtrack')
config_path = os.path.join(config_dir, 'config.yml')

os.makedirs(f"{config_dir}", exist_ok=True)

default_config = {
    "guild": None,
    "token": None,
    "client_id": None,
    "role": None,
}

if os.path.exists(config_path) and not '--reconfigure' in sys.argv:
    with open(config_path, "r") as file:
        config = yaml.full_load(file)
else:
    config = auto_configure()
    if config == None:
        if not '--reconfigure' in sys.argv:
            logger.critical(f'Configuration file does not exist!\n -> You must either run interactive configuration, or copy an existing configuration file to {config_path}.')
        sys.exit(10)
    else:
        with open(config_path, "w") as file:
            yaml.dump(config, file)
        logger.info('Configuration complete!')

# Global Variables
try:
    LOCKED_GUILDS = [int(config["guild"])]
    PERMISSION_ROLE = [int(config["role"])]
except ValueError:
    logger.error(f'Either `guild` or `role` is not a valid integer! Edit {config_path} or run with `--reconfigure` and be sure to use valid IDs.')
    sys.exit(20)
TRACK_PATH = os.path.join(BaseDirectory.xdg_data_home, 'soundtrack')

guild = None
role = None
requests = 0
connected = False

# Load Tracklist
with open(os.path.join(TRACK_PATH, 'index.yml')) as file:
    index = yaml.full_load(file)

tracks = [name for name in index]

data_dir = os.path.join(BaseDirectory.xdg_data_home, 'soundtrack')
os.makedirs(f"{data_dir}", exist_ok=True)
os.makedirs(TRACK_PATH, exist_ok=True)

# Events
@bot.event
async def on_ready():
    """ On Ready Event """
    global config
    msg = [
        " ",
        " --------------------",
        f" 🎜 Soundtrack v{pkg_resources.get_distribution(__package__).version}",
        "    © 2023 Krafter",
        "    MIT License",
        " --------------------",
        " ",
    ]
    for i in msg:
        logger.info(i)
    logger.debug(f'Logged in as {bot.user}')
    
    global guild
    global role
    global config_path
    try:
        guild = bot.get_guild(int(config["guild"]))
        if guild == None:
            raise ValueError('Guild is None')
        logger.success(f'Connected with Guild: {guild.name} (ID: {guild.id})')
        try:
            role = guild.get_role(int(config["role"]))
            if role == None:
                raise ValueError('Role is None')
            logger.success(f'Connected with Role: {role.name} (ID: {role.id})')
        except ValueError:
            logger.warning(f'Could not fetch role with ID {config["role"]}! Edit {config_path} or run with `--reconfigure`.')
    except ValueError:
        logger.warning(f'Could not fetch guild with ID {config["guild"]}! Edit {config_path} or run with `--reconfigure`.')
    
    if guild in bot.guilds:
        logger.success(f'Connected and ready to use!')
    else:
        logger.success(f'Invite to your Guild: {get_invite_url(config["client_id"])}')
    
    for g in bot.guilds:
        if g != guild:
            await g.leave()

@bot.event
async def on_guild_join(new_guild: nextcord.Guild):
    global guild
    if new_guild.id != guild.id:
        await new_guild.leave()

# Commands
@bot.slash_command(description='Upload a Soundtrack', dm_permission=False, guild_ids=LOCKED_GUILDS)
async def upload(interaction: nextcord.Interaction, 
    title: str = nextcord.SlashOption(description='The title for this soundtrack', min_length=3, max_length=45, required=True),
    intro: nextcord.Attachment = nextcord.SlashOption(description='Track to play at start of soundtrack', required=True),
    loop: nextcord.Attachment = nextcord.SlashOption(description='Track to loop once `intro` ends', required=True),
    delay: int = nextcord.SlashOption(description='Delay between end of Intro and start of Loop (default 0)', choices=[0,1,2,3,4,5,6,7,8,9,10], default=0, required=False)):
    """ Slash Command: Allows users to upload tracks and saves them to disk. """
    global config
    global role
    if role in interaction.user.roles:
        global requests
        requests += 1
        r = requests
        logger.debug(f'{r}: Processing Soundtrack Upload Request...')
        # Ensure Title is okay
        if '#' in title or '>' in title or '-' in title or '.' in title:
            await interaction.send(messages.badname, ephemeral=True)
            return
        # Ensure files are mp3 files
        if intro.content_type != 'audio/mpeg' or loop.content_type != 'audio/mpeg':
            await interaction.send(messages.notaudio, ephemeral=True)
            logger.debug(f'{r}: Soundtrack Upload Request Cancelled. Media was not of proper type.')
            return
        # Get Index
        global TRACK_PATH
        index_path = os.path.join(TRACK_PATH, 'index.yml')
        await interaction.response.defer()
        try:
            with open(index_path, "r") as file:
                index = yaml.full_load(file)
            if index == None:
                raise FileNotFoundError
            logger.debug(f'{r}: Found existing Track Index at {index_path}')
        except FileNotFoundError:
            logger.debug(f'{r}: No Track Index at {index_path}, will save new index to it.')
            index = {}
        # Save Files
        intro_path = os.path.join(TRACK_PATH, f'{str(uuid.uuid4())}.mp3')
        loop_path = os.path.join(TRACK_PATH, f'{str(uuid.uuid4())}.mp3')
        await intro.save(intro_path)
        await loop.save(loop_path)
        logger.debug(f'{r}: Saved Soundtrack Files successfully')
        # Add to index
        index[title] = {
            'intro': intro_path,
            'loop': loop_path,
            'delay': delay,
        }
        global tracks
        if title not in tracks:
            tracks.append(title)
        with open(index_path, "w+") as file:
            index_current = yaml.full_load(file)
            if index_current == None:
                index_current = {}
            index_new = index_current | index
            yaml.dump(index_new, file)
        logger.debug(f'{r}: Added to index')
        # Report Success
        logger.success(f'Added Soundtrack: "{title}"!')
        await interaction.send(f'**Added new Soundtrack!**\n*{title}* is now a part of your library.')
    else:
        await interaction.send(messages.noperm, ephemeral=True)

@bot.slash_command(description='Play a soundtrack from your library', dm_permission=False, guild_ids=LOCKED_GUILDS)
async def play(interaction: nextcord.Interaction, track: str = nextcord.SlashOption(description='The name of the soundtrack to play', required=True)):
    await interaction.send(f'Testing, you picked track: {track}')

@play.on_autocomplete("track")
async def track_autocomplete(interaction: nextcord.Interaction, track: str):
    global tracks
    if not track:
        await interaction.response.send_autocomplete(tracks)
        return
    near_tracks = [t for t in tracks if t.lower().startswith(track.lower())]
    if near_tracks == []:
        near_tracks = [t for t in tracks if track.lower() in t.lower()]
    await interaction.response.send_autocomplete(near_tracks)

bot.run(config["token"])