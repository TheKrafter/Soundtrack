# 
# Soundtrack 
# Copyright (c) 2023 Krafter Developer
# 
from logging42 import logger
from requests.models import PreparedRequest


def get_invite_url(client_id: str):
    """ Creates a Bot Invite URL based on the given `client_id` """
    base_url = "https://discord.com/api/oauth2/authorize"
    params = {
        "client_id": client_id,
        "permissions": "3147776",
        "scope": "bot",
    }
    r = PreparedRequest()
    r.prepare_url(base_url, params)
    return r.url


def auto_configure():
    """ Interactive Configuration """
    logger.info('Running interactive configuration...')
    if input('Continue? [Y/n] ').strip(' \n').lower() != 'n':
        while True:
            print('1. Obtain a bot token from https://discord.com/developers and paste it below.')
            token = input(' -> ').strip(' \n')
            print('2. Paste your Application ID from https://discord.com/developers below')
            client_id = input(' -> ').strip(' \n')
            print('3. Paste the ID of the Guild this bot will be locked to.')
            guild = input(' -> ').strip(' \n')
            print('4. Paste the ID of the Role in said Guild that has permission to upload and edit soundtracks.')
            role = input(' -> ').strip(' \n')
            print('5. Should this bot be specifically locked to your guild? If not, you can still only upload and delete tracks within said guild.')
            if input(' -> [Y/n] ').strip(' \n').lower() != 'n':
                locked = False
            else:
                locked = True

            print(f'\nDoes this look right?\n1. Bot Token - {token}\n2. Application ID - {client_id}\n3. Guild ID - {guild}\n4. Role ID - {role}')
            if input(' -> [Y/n] ').strip(' \n').lower() != 'n':
                break
        result = {
            "guild": guild,
            "token": token,
            "client_id": client_id,
            "role": role,
            "locked": locked,
        }
        logger.info('Interactive configuration complete.')
        return result
    else:
        logger.warning('Cancelled interactive configuration.')
        return None
