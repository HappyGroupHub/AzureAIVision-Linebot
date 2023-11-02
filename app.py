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
        print(" Caption:")
        print("   '{}', Confidence {:.4f}".format(result.caption.content, result.caption.confidence))

    if result.text is not None:
        print(" Text:")
        for line in result.text.lines:
            points_string = "{" + ", ".join([str(int(point)) for point in line.bounding_polygon]) + "}"
            print("   Line: '{}', Bounding polygon {}".format(line.content, points_string))
            for word in line.words:
                points_string = "{" + ", ".join([str(int(point)) for point in word.bounding_polygon]) + "}"
                print("     Word: '{}', Bounding polygon {}, Confidence {:.4f}"
                      .format(word.content, points_string, word.confidence))

else:
    error_details = ai_vision.ImageAnalysisErrorDetails.from_result(result)
    print(" Analysis failed.")
    print("   Error reason: {}".format(error_details.reason))
    print("   Error code: {}".format(error_details.error_code))
    print("   Error message: {}".format(error_details.message))
