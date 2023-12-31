import datetime
import math
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

# Paste your endpoint for the webhook here.
# You can use ngrok to get a free static endpoint now!
# Find out more here: https://ngrok.com/
# Notes: Make sure the webhook url is started with https:// and ended without a slash (/)
webhook_url: ''
# Port for the webhook to listen on. Default is 5000.
# If you change this, make sure to change the port in your reverse proxy as well.
webhook_port: 5000

# Azure AI Vision API Key
vision_key: ""
vision_endpoint: ""

# Azure OpenAI API Key
aoai_key: ''
aoai_endpoint: ''

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
                'webhook_url': data['webhook_url'],
                'webhook_port': data['webhook_port'],
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


def get_cosine_similarity(vector1, vector2):
    """Get the cosine similarity between two vectors.

    :param list vector1: Vector 1
    :param list vector2: Vector 2
    :return float cosine_similarity: Cosine similarity
    """
    dot_product = 0
    length = min(len(vector1), len(vector2))

    for i in range(length):
        dot_product += vector1[i] * vector2[i]

    magnitude1 = math.sqrt(sum(x * x for x in vector1))
    magnitude2 = math.sqrt(sum(x * x for x in vector2))

    return dot_product / (magnitude1 * magnitude2)


def get_top_n_similar_images(target_vector, imageset_vector, n=3):
    """Get top n similar images from imageset.

    :param list target_vector: Given vector, can be image vector or text vector
    :param list imageset_vector: Imageset vector
    :param int n: Number of similar images, default is 3
    :return list top_n_similar_images: Top n similar images
    """
    similarity_dict = {}
    for image in imageset_vector:
        similarity = get_cosine_similarity(target_vector, imageset_vector[image])
        similarity_dict[image] = similarity
    top_n_similar_images = sorted(similarity_dict.items(), key=lambda x: x[1], reverse=True)[:n]
    return top_n_similar_images
