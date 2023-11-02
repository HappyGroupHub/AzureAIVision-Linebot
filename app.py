import azure.ai.vision as ai_vision

import utilities as utils

config = utils.read_config()
service = ai_vision.VisionServiceOptions(key=config['vision_key'],
                                         endpoint=config['vision_endpoint'])

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
