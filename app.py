import azure.ai.vision as ai_vision
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, \
    TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, FollowEvent

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
service = ai_vision.VisionServiceOptions(key=config['vision_key'],
                                         endpoint=config['vision_endpoint'])


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
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        message_received = event.message.text
        reply_token = event.reply_token

        if message_received == "test":
            reply_message = f"Hello World!"
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


analysis_options = ai_vision.ImageAnalysisOptions()
analysis_options.features = (
    ai_vision.ImageAnalysisFeature.CAPTION
)
analysis_options.language = "en"

test_source = ai_vision.VisionSource(
    url="https://learn.microsoft.com/zh-tw/azure/ai-services/computer-vision/media/quickstarts/presentation.png")

image_analyzer = ai_vision.ImageAnalyzer(service, test_source, analysis_options)
result = image_analyzer.analyze()

if result.reason == ai_vision.ImageAnalysisResultReason.ANALYZED:
    if result.caption is not None:
        caption = result.caption.content
        confidence = result.caption.confidence
        print(f"Caption: {caption}")
        print(f"Confidence: {confidence}")
else:
    error_details = ai_vision.ImageAnalysisErrorDetails.from_result(result)
    print("Analysis failed.")
    print(f"   Error reason: {error_details.reason}")
    print(f"   Error code: {error_details.error_code}")
    print(f"   Error message: {error_details.message}")

if __name__ == '__main__':
    uvicorn.run(app, port=5000)
