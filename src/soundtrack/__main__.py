# 
# Soundtrack 
# Copyright (c) 2023 Krafter Developer
# 
from logging42 import logger

import os
import sys
import yaml
import pkg_resources

from xdg import BaseDirectory
import nextcord
from nextcord.ext import commands

from .internal.util import verify_config, auto_configure

logger.debug('Starting...')

# Bot Definition
intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents)

# Load Config
global config
global config_dir
global config_path
config = None
config_dir = os.path.join(BaseDirectory.xdg_config_home, 'soundtrack')
config_path = os.path.join(config_dir, 'config.yml')

os.makedirs(f"{config_dir}", exist_ok=True)

default_config = {
    "guild": None,
    "token": None,
    "role": None,
}

if os.path.exists(config_path):
    with open(config_path, "r") as file:
        global config
        config = yaml.full_load(file)

    verify_config(config, default_config)
else:
    auto_configure() #TODO

data_dir = os.path.join(BaseDirectory.xdg_data_home, 'soundtrack')
os.makedirs(f"{data_dir}", exist_ok=True)

# Events
@bot.event
async def on_ready():
    """ On Ready Event """
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

# Commands
@bot.slash_command(description='Upload a Track', dm_permission=False)
async def upload(interaction: nextcord.Interaction, name: nextcord.SlashOption(description='The title for this track set'))