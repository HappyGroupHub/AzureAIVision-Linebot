import sys
from os.path import exists

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
