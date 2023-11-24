from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, \
    TextMessage, ImageMessage, QuickReply, MessageAction, QuickReplyItem
from linebot.v3.webhooks import MessageEvent, TextMessageContent, FollowEvent, ImageMessageContent

import ai_vision
import aoai
import utilities as utils

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

config = utils.read_config()
configuration = Configuration(access_token=config['line_channel_access_token'])
handler = WebhookHandler(config['line_channel_secret'])

config = utils.read_config()
webhook_url = config['webhook_url']
imageset_path = './example_imageset/'
user_action = {}


@app.get("/getimage/{image_name}")
async def get_image(image_name: str):
    image_path = Path(imageset_path + image_name)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(image_path)


@app.post("/callback")
async def callback(request: Request):
    """Callback function for line webhook."""

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()

    # handle webhook body
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """Handle text message event."""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        message_received = event.message.text
        user_id = event.source.user_id
        reply_token = event.reply_token

        if message_received == "Analyze Image":
            user_action[user_id] = 'analyze_image'
            reply_message = f"Please upload ONE image you wished to analyze.\n" \
                            f"Processing might take a while, please be patient for the result."
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
                )
            )
        elif message_received == "Generate Image":
            user_action[user_id] = 'generate_image'
            reply_message = f"How would you like to generate the image?"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message,
                                          quick_reply=QuickReply(items=[QuickReplyItem(
                                              action=MessageAction(
                                                  label="AI Imagination",
                                                  text="Generate image randomly with AI imagination")),
                                              QuickReplyItem(
                                                  action=MessageAction(
                                                      label="Find Similar Image",
                                                      text="Find the most similar image")
                                              )]))]
                )
            )
        elif user_id in user_action:
            if user_action[user_id] == 'generate_image':
                if message_received == 'Generate image randomly with AI imagination':
                    user_action[user_id] = 'generate_image_aoai'
                elif message_received == 'Find the most similar image':
                    user_action[user_id] = 'find_similar_image'
                reply_message = f"Now tell me more about this image!\n" \
                                f"Processing might take a while, please be patient for the result."
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=reply_message)]
                    )
                )
            elif user_action[user_id] == 'generate_image_aoai':
                user_action[user_id] = 'processing'
                image_url = aoai.generate_image_with_text(message_received)['image_url']
                user_action.pop(user_id)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[ImageMessage(original_content_url=image_url,
                                               preview_image_url=image_url)]
                    )
                )
            elif user_action[user_id] == 'find_similar_image':
                user_action[user_id] = 'processing'
                text_vector = ai_vision.get_vectorize_text(message_received)
                imageset_vector = ai_vision.vectorize_imageset(imageset_path)
                similar_images = utils.get_top_n_similar_images(text_vector, imageset_vector, n=1)
                similar_image, similarity = similar_images[0]
                similar_image_url = f'{webhook_url}/getimage/{similar_image}'.replace(' ', '%20')
                user_action.pop(user_id)
                reply_message = f"Top similar image: {similar_image}\n" \
                                f"Similarity: {similarity}"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=reply_message),
                                  ImageMessage(original_content_url=similar_image_url,
                                               preview_image_url=similar_image_url)]
                    )
                )
            elif user_action[user_id] == 'processing':
                reply_message = f"We're still processing your previous request, " \
                                f"please wait for the result patiently."
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=reply_message)]
                    )
                )
        else:
            reply_message = f"Please open the menu to select which service you want to use."
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
                )
            )


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """Handle image message event."""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        message_id = event.message.id
        reply_token = event.reply_token
    if user_id in user_action:
        if user_action[user_id] == 'analyze_image':
            user_action.pop(user_id)
            image_path = utils.download_file_from_line(message_id, 'image')
            analysis = ai_vision.get_image_caption(file_name=image_path)
            image_vector = ai_vision.get_vectorize_image(image_path)
            imageset_vector = ai_vision.vectorize_imageset('example_imageset')
            similar_images = utils.get_top_n_similar_images(image_vector, imageset_vector, n=1)
            similar_image, similarity = similar_images[0]
            similar_image_url = f'{webhook_url}/getimage/{similar_image}'.replace(' ', '%20')
            reply_message = f"Caption: {analysis['caption']}\n" \
                            f"Confidence: {analysis['confidence']}\n" \
                            f"Top similar image: {similar_image}\n" \
                            f"Similarity: {similarity}"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message),
                              ImageMessage(original_content_url=similar_image_url,
                                           preview_image_url=similar_image_url)]
                )
            )
        elif user_action[user_id] == 'processing':
            reply_message = f"We're still processing your previous request, " \
                            f"please wait for the result patiently."
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
                )
            )
        else:
            reply_message = f"Please open the menu to select which service you want to use."
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
                )
            )


@handler.add(FollowEvent)
def handle_follow(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        reply_token = event.reply_token
        reply_message = f"Hello World!"
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply_message)]
            )
        )


if __name__ == '__main__':
    uvicorn.run(app, port=config['webhook_port'])
