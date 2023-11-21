import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, \
    TextMessage, ImageMessage
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
    allow_methods=["POST"],
    allow_headers=["*"],
)

config = utils.read_config()
configuration = Configuration(access_token=config['line_channel_access_token'])
handler = WebhookHandler(config['line_channel_secret'])

config = utils.read_config()
user_action = {}


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
            reply_message = f"Tell me what image would you like to generate today!\n" \
                            f"Processing might take a while, please be patient for the result."
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
                )
            )
        elif user_id in user_action:
            if user_action[user_id] == 'generate_image':
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
            reply_message = f"Caption: {analysis['caption']}\n" \
                            f"Confidence: {analysis['confidence']}"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_message)]
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
    uvicorn.run(app, port=5000)
