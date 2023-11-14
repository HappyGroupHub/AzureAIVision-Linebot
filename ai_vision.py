import azure.ai.vision as sdk

import utilities as utils

config = utils.read_config()
service = sdk.VisionServiceOptions(key=config['vision_key'],
                                   endpoint=config['vision_endpoint'])

analysis_options = sdk.ImageAnalysisOptions()
analysis_options.features = (
    sdk.ImageAnalysisFeature.CAPTION
)
analysis_options.language = "en"


def get_image_caption(image_url=None, file_name=None):
    """Get image caption from Azure AI Vision API.

    :param file_name: Image file path
    :param str image_url : Image URL
    :return dict response : Response from Azure AI Vision API
    """
    image_source = None
    if image_url is not None:
        image_source = sdk.VisionSource(url=image_url)
    if file_name is not None:
        image_source = sdk.VisionSource(filename=file_name)
    image_analyzer = sdk.ImageAnalyzer(service, image_source, analysis_options)
    result = image_analyzer.analyze()
    response = {}
    if result.reason == sdk.ImageAnalysisResultReason.ANALYZED:
        response['status'] = 'success'
        if result.caption is not None:
            response['caption'] = result.caption.content
            response['confidence'] = result.caption.confidence
    else:
        response['status'] = 'failed'
        error_details = sdk.ImageAnalysisErrorDetails.from_result(result)
        print("Analysis failed.")
        print(f"   Error reason: {error_details.reason}")
        print(f"   Error code: {error_details.error_code}")
        print(f"   Error message: {error_details.message}")
    return response
