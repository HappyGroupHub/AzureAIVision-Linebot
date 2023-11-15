import datetime
import os
import sys
from os.path import exists

import requests
import yaml
from yaml import SafeLoader


def config_file_generator():
    """Generate the template of config file"""
    with open('config.yml', 'w', encoding="utf8") as file:
        file.write("""# ++--------------------------------++
# | AzureAIVision Linebot            |
# | Made by LD                       |
# ++--------------------------------++

# Azure AI Vision API Key
vision_key: ""
vision_endpoint: ""

# Azure OpenAI API Key
aoai_key: '9197f1e023364cd489f3c29e71dceaa4'
aoai_endpoint: 'https://20th-ld-aivision-aoai.openai.azure.com/'

# Line Channel Access Token & Secret
line_channel_access_token: ""
line_channel_secret: ""
"""
                   )
        file.close()
    sys.exit()


def read_config():
    """Read config file.

    Check if config file exists, if not, create one.
    if exists, read config file and return config with dict type.

    :rtype: dict
    """
    if not exists('./config.yml'):
        print("Config file not found, create one by default.\nPlease finish filling config.yml")
        with open('config.yml', 'w', encoding="utf8"):
            config_file_generator()

    try:
        with open('config.yml', encoding="utf8") as file:
            data = yaml.load(file, Loader=SafeLoader)
            config = {
                'vision_key': data['vision_key'],
                'vision_endpoint': data['vision_endpoint'],
                'aoai_key': data['aoai_key'],
                'aoai_endpoint': data['aoai_endpoint'],
                'line_channel_access_token': data['line_channel_access_token'],
                'line_channel_secret': data['line_channel_secret']
            }
            file.close()
            return config
    except (KeyError, TypeError):
        print(
            "An error occurred while reading config.yml, please check if the file is corrected filled.\n"
            "If the problem can't be solved, consider delete config.yml and restart the program.\n")
        sys.exit()


def download_file_from_line(message_id, message_type):
    """Get file binary and save them in PC.

    Use to download files from LINE.

    :param message_id: message id from line
    :param message_type: message type from line
    :return str: file path
    """
    config = read_config()
    url = f'https://api-data.line.me/v2/bot/message/{message_id}/content'
    headers = {'Authorization': f'Bearer {config["line_channel_access_token"]}'}
    source = requests.get(url, headers=headers)

    file_type = {
        'image': 'jpg',
        'video': 'mp4',
        'audio': 'm4a',
    }
    path = f'./downloads'
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = \
        f"{path}/{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.{file_type[message_type]}"
    with open(file_path, 'wb') as fd:
        for chunk in source.iter_content():
            fd.write(chunk)
    return file_path
