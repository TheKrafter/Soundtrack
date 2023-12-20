# 
# Soundtrack 
# Copyright (c) 2023 Krafter Developer
# 
from logging42 import logger

import os
import sys
import yaml
import pkg_resources

import xdg
import nextcord
from nextcord.ext import commands

logger.debug('Starting...')

# Bot Definition
intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents)

# Load Config
global config
config = None

config_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, 'soundtrack')

os.makedirs(f"{config_dir}", exist_ok=True)

with open(os.path.join(config_dir, 'config.yml'), "r") as file:
    global config
    config = yaml.full_load(file)


# Events
@bot.event
async def on_ready():
    """ On Ready Event """
    logger.debug(f'Logged in as {bot.user}')
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
