# 
# Soundtrack 
# Copyright (c) 2023 Krafter Developer
# 
from logging42 import logger

import os
import sys
import yaml
import uuid
import time
import pkg_resources
from typing import Optional

from xdg import BaseDirectory
import nextcord
from nextcord.ext import commands, tasks

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
        '-c, --config   : Print the path of the Configuration File',
        '-d, --data     : Print the path of the Data Directory (where tracks are stored)',
        '--reconfigure  : Re-run interactive configuration',
        '--verbose      : Show debugging Log messages',
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
                f"    {get_invite_url(cfg['client_id'])}",
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
elif '--data' in sys.argv or '-d' in sys.argv:
    print(os.path.join(BaseDirectory.xdg_data_home, 'soundtrack', ''))
    sys.exit(0)

if not '--verbose' in sys.argv:
    logger.remove(1)
    logger.add(sys.stdout, level="INFO")

logger.debug('Starting...')

# Bot Definition
intents = nextcord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True
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
TRACK_PATH = os.path.join(BaseDirectory.xdg_data_home, 'soundtrack')

guild = None
role = None
requests = 0
voice_client = None
stop_when_looped = False
block_disconnect = False

# Load Tracklist
try:
    with open(os.path.join(TRACK_PATH, 'index.yml')) as file:
        index = yaml.full_load(file)
    if index == None:
        index = {}
    tracks = [name for name in index]
except FileNotFoundError:
    tracks = []

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

    if 'locked' in config:
        if not config['locked']:
            logger.info('Soundtrack is not guild-locked!')
    else:
        for g in bot.guilds:
            if g != guild:
                await g.leave()

    global auto_disconnect
    if not auto_disconnect.is_running():
        await auto_disconnect.start()
    
    global update_tracks
    if not update_tracks.is_running():
        await update_tracks.start()

@bot.event
async def on_guild_join(new_guild: nextcord.Guild):
    global guild
    if new_guild.id != guild.id:
        await new_guild.leave()

@tasks.loop(seconds=5)
async def auto_disconnect():
    global voice_client
    global block_disconnect
    global guild
    try:
        if len(voice_client.channel.members) <= 1 and guild.me in voice_client.channel.members and voice_client.is_connected() and not block_disconnect:
            voice_client.stop()
            await voice_client.disconnect()
            logger.info('🎜 Automatically Disconnected.')
        else:
            block_disconnect = False
    except ValueError:
        pass
    except AttributeError:
        pass
    except nextcord.errors.ClientException:
        pass

@tasks.loop(seconds=5)
async def update_tracks():
    global tracks
    global TRACK_PATH
    logger.debug('🎜 Refreshing Track List...')
    with open(os.path.join(TRACK_PATH, 'index.yml'), "r") as file:
        index = yaml.full_load(file)
    new_tracks = []
    for t in index:
        new_tracks.append(t)
    tracks = new_tracks
    logger.debug('🎜 Refreshed Track List from Disk')

try:
    UPLOADING_GUILD = int(config['guild'])
except ValueError:
    logger.error(f'{config["guild"]} is not a valid Guild ID! Either edit {config_path} manually, or run with `--reconfigure`!')
    sys.exit(20)

# Commands
@bot.slash_command(description='Upload a Soundtrack', dm_permission=False, guild_ids=[UPLOADING_GUILD])
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
        await interaction.send(f'**Added new Soundtrack!**\n*{title}* is now a part of the library.')
    else:
        await interaction.send(messages.noperm, ephemeral=True)

@bot.slash_command(description='Play a soundtrack from the library', dm_permission=False)
async def play(interaction: nextcord.Interaction, track: str = nextcord.SlashOption(description='The name of the soundtrack to play', required=True)):
    global tracks
    if not track in tracks:
        await interaction.send(messages.badtrack, ephemeral=True)
    else:
        global voice_client
        global guild
        if interaction.user.voice == None:
            await interaction.send(messages.novoice, ephemeral=True)
            return
        elif interaction.user.voice.channel == None or interaction.user.voice.channel.guild.id != guild.id:
            await interaction.send(messages.novoice, ephemeral=True)
            return
        elif interaction.user.voice.mute or interaction.user.voice.suppress:
            await interaction.send(messages.muted, ephemeral=True)
            return
        
        if voice_client == None:
            # Connect to Voice
            voice_client = await interaction.user.voice.channel.connect(reconnect=True)
        
        global TRACK_PATH
        with open(os.path.join(TRACK_PATH, 'index.yml'), "r") as file:
            index = yaml.full_load(file)
        if track not in index:
            await interaction.send(messages.badtrack.replace('.', '!'))
            return
        if not os.path.exists(index[track]["intro"]) or not os.path.exists(index[track]["loop"]):
            await interaction.send(messages.trackfiles_missing)
            return
        
        await interaction.send(f'**🎜 Playing Soundtrack**\n> {track}')

        if voice_client.is_playing():
            voice_client.stop()
        if not voice_client.is_connected():
            # Reconnect if not connected
            voice_client = await interaction.user.voice.channel.connect(reconnect=True)
        if voice_client.channel != interaction.user.voice.channel:
            voice_client.move_to(interaction.user.voice.channel)

        global current_loop 
        global current_loop_delay
        global already_delayed
        current_loop = index[track]["loop"]
        current_loop_delay = int(index[track]["delay"])
        already_delayed = False
        def play_loop(error):
            global voice_client
            global current_loop
            global current_loop_delay
            global already_delayed
            global stop_when_looped
            if voice_client.is_connected() and not stop_when_looped:
                if not already_delayed:
                    time.sleep(current_loop_delay)
                    already_delayed = True
                logger.info('🎜 Playing Soundtrack Loop')
                try:
                    voice_client.play(nextcord.FFmpegPCMAudio(current_loop), after=play_loop)
                except nextcord.errors.ClientException:
                    pass
            else:
                stop_when_looped = False
                logger.info('🎜 Soundtrack Ended.')
        
        await interaction.guild.change_voice_state(channel=interaction.user.voice.channel, self_deaf=True, self_mute=False)

        logger.info('🎜 Playing Soundtrack Intro')
        global block_disconnect
        block_disconnect = True
        voice_client.play(nextcord.FFmpegPCMAudio(index[track]["intro"]), after=play_loop)

@bot.slash_command(description='Stop playing soundtrack', dm_permission=False)
async def pause(interaction: nextcord.Interaction, when: str = nextcord.SlashOption(description='When to stop the track', choices=['Now', 'End of File'], default='Now', required=False)):
    global voice_client
    global guild
    if voice_client == None:
        await interaction.send(messages.notplaying, ephemeral=True)
        return
    elif not voice_client.is_playing():
        await interaction.send(messages.notplaying, ephemeral=True)
        return
    elif interaction.user.voice == None:
        await interaction.send(messages.novoice, ephemeral=True)
        return
    elif interaction.user.voice.channel == None or interaction.user.voice.channel.guild.id != guild.id:
        await interaction.send(messages.novoice, ephemeral=True)
        return
    elif interaction.user.voice.mute or interaction.user.voice.suppress:
        await interaction.send(messages.muted, ephemeral=True)
        return

    if when == 'Now':
        voice_client.pause()
        await interaction.send(f'**🎜 Paused**')
    elif when == 'End of File':
        global stop_when_looped
        stop_when_looped = True
        await interaction.send(f'**🎜** Pausing at *End of File*')

@bot.slash_command(description='Continue playing soundtrack', dm_permission=False)
async def resume(interaction: nextcord.Interaction):
    global voice_client
    if voice_client == None:
        await interaction.send(messages.notplaying, ephemeral=True)
        return
    elif voice_client.is_paused():
        voice_client.resume()
        await interaction.send('**🎜 Resumed**')

@bot.slash_command(description='Leave the Voice Channel', dm_permission=False)
async def stop(interaction: nextcord.Interaction):
    global voice_client
    if voice_client == None:
        await interaction.send(messages.notplaying, ephemeral=True)
        return
    elif voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        await interaction.send('**🎜 Stopped**')
    else:
        await interaction.send(messages.notplaying, ephemeral=True)

@bot.slash_command(description='Delete a soundtrack from the library (stops playback)', dm_permission=False, guild_ids=[UPLOADING_GUILD])
async def delete(interaction: nextcord.Interaction, track: str = nextcord.SlashOption(description='The name of the soundtrack to delete', required=True)):
    global role
    global voice_client
    if role in interaction.user.roles:
        if voice_client != None:
            voice_client.stop()
            await voice_client.disconnect()
        global TRACK_PATH
        global tracks
        with open(os.path.join(TRACK_PATH, 'index.yml'), "r") as file:
            index = yaml.full_load(file)
        if track in index:
            try:
                for i in range(len(tracks) - 1):
                    if tracks[i] == track:
                        del tracks[i]
                del index[track]
                os.remove(index[track]["intro"])
                os.remove(index[track]["loop"])
            except ValueError:
                pass
            except BaseException as e:
                await interaction.send(f'**Could not delete Track!** Unexpected error occurred: \n```\n{e}\n```')
                return
            await interaction.send(f'Removed soundtrack *{track}* from library.')
        else:
            await interaction.send(messages.badtrack, ephemeral=True)
    else:
        await interaction.send(messages.noperm, ephemeral=True)

@bot.slash_command(description='Rename a soundtrack in the library (stops playback)', dm_permission=False, guild_ids=[UPLOADING_GUILD])
async def rename(interaction: nextcord.Interaction,
    old: str = nextcord.SlashOption(description='The current name of the track', required=True),
    new: str = nextcord.SlashOption(description='The new name of the soundtrack', required=True, min_length=3, max_length=45)):
    global role
    global voice_client
    if role in interaction.user.roles:
        if voice_client != None:
            voice_client.stop()
            await voice_client.disconnect()
        global TRACK_PATH
        global tracks
        with open(os.path.join(TRACK_PATH, 'index.yml'), "r") as file:
            index = yaml.full_load(file)
        if old in index:
            if '#' in new or '>' in new or '.' in new or '-' in new:
                await interaction.send(messages.badrename, ephemeral=True)
            else:
                for i in range(len(tracks) - 1):
                    if tracks[i] == old:
                        tracks.pop(i)
                index[new] = index.pop(old)
                tracks.append(new)
                with open(os.path.join(TRACK_PATH, 'index.yml'), "w") as file:
                    yaml.dump(index, file)
                await interaction.send(f'Renamed *{nextcord.utils.escape_markdown(old)}* to *{nextcord.utils.escape_markdown(new)}*.')
        else:
            await interaction.send(messages.badtrack, ephemeral=True)
    else:
        await interaction.send(messages.noperm, ephemeral=True)

@rename.on_autocomplete("old")
@delete.on_autocomplete("track")
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