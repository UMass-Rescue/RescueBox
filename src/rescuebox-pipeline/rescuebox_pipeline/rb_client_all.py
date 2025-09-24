import sys
from pathlib import Path

from rescue_box_api_client import Client
from rescue_box_api_client.api.audio import (
    rb_audio_api_app_metadata_get,
    rb_audio_api_routes_get,
    rb_audio_transcribe_post,
    rb_audio_transcribe_task_schema_get,
)
from rescue_box_api_client.api.manage import list_plugins_post
from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_api_app_metadata_get,
    rb_text_summarization_api_routes_get,
    rb_text_summarization_summarize_post,
    rb_text_summarization_summarize_task_schema_get,
)
from rescue_box_api_client.models import BatchTextResponse
from rescue_box_api_client.models.audio_directory import AudioDirectory
from rescue_box_api_client.models.audio_input import AudioInput
from rescue_box_api_client.models.body_audio_transcribe_post import (
    BodyAudioTranscribePost,
)
from rescue_box_api_client.models.body_text_summarization_summarize_post import (
    BodyTextSummarizationSummarizePost,
)
from rescue_box_api_client.models.directory_input import DirectoryInput
from rescue_box_api_client.models.file_input import FileInput
from rescue_box_api_client.models.deepfake_detection_predict_inputs import DeepfakeDetectionPredictInputs
from rescue_box_api_client.models.text_summarization_summarize_inputs import TextSummarizationSummarizeInputs
from rescue_box_api_client.models.text_summarization_summarize_parameters import TextSummarizationSummarizeParameters
from rescue_box_api_client.models.text_input import TextInput
from rescue_box_api_client.models.validation_error import ValidationError


from rescue_box_api_client.models.age_gender_predict_inputs import AgeGenderPredictInputs
from rescue_box_api_client.models.deepfake_detection_predict_parameters import DeepfakeDetectionPredictParameters
from rescue_box_api_client.models.body_age_gender_predict_post import BodyAgeGenderPredictPost
from rescue_box_api_client.models.body_deepfake_detection_predict_post import BodyDeepfakeDetectionPredictPost
from rescue_box_api_client.models.body_face_match_bulkupload_post import BodyFaceMatchBulkuploadPost
from rescue_box_api_client.models.body_face_match_deletecollection_post import BodyFaceMatchDeletecollectionPost
from rescue_box_api_client.models.body_face_match_findfacebulk_post import BodyFaceMatchFindfacebulkPost
from rescue_box_api_client.models.body_ufdr_mounter_mount_post import BodyUfdrMounterMountPost
from rescue_box_api_client.models.ufdr_inputs import UFDRInputs
from rescue_box_api_client.models.ufdr_parameters import UFDRParameters
from rescue_box_api_client.models.bulk_upload_inputs import BulkUploadInputs
from rescue_box_api_client.models.bulk_upload_parameters import BulkUploadParameters
from rescue_box_api_client.models.delete_collection_inputs import DeleteCollectionInputs
from rescue_box_api_client.models.delete_collection_parameters import DeleteCollectionParameters
from rescue_box_api_client.models.find_face_bulk_inputs import FindFaceBulkInputs
from rescue_box_api_client.models.find_face_bulk_parameters import FindFaceBulkParameters

from rescue_box_api_client.models.image_directory import ImageDirectory

from rescue_box_api_client.api.age_gender import (
    rb_age_gender_api_app_metadata_get,
    rb_age_gender_api_routes_get,
    rb_age_gender_predict_post,
    rb_age_gender_predict_task_schema_get,
)
from rescue_box_api_client.api.deepfake_detection import (
    rb_deepfake_detection_api_app_metadata_get,
    rb_deepfake_detection_api_routes_get,
    rb_deepfake_detection_predict_post,         
    rb_deepfake_detection_predict_task_schema_get,
)
from rescue_box_api_client.api.face_match import (
    rb_face_match_api_app_metadata_get,
    rb_face_match_api_routes_get,
    rb_face_match_bulkupload_post,
    rb_face_match_bulkupload_task_schema_get,
    rb_face_match_deletecollection_post,
    rb_face_match_deletecollection_task_schema_get,
    rb_face_match_findfacebulk_post,
    rb_face_match_findfacebulk_task_schema_get,
)
from rescue_box_api_client.api.ufdr_mounter import (
    rb_ufdr_mounter_api_app_metadata_get,
    rb_ufdr_mounter_api_routes_get,
    rb_ufdr_mounter_mount_post,
    rb_ufdr_mounter_mount_task_schema_get,
)


# assume rescuebox  run_server is up and running on port 8000
# create client and run the audio plugin api calls

client = Client(base_url="http://localhost:8000", verify_ssl=False)

list_plugins = list_plugins_post.sync(
    client=client,
    streaming=False,
)
print("list plugins", list_plugins)

######## ufdr mounter plugin calls ##############

rb_ufdr_mounter_api_app_metadata = rb_ufdr_mounter_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print("ufdr mounter app_metadata", rb_ufdr_mounter_api_app_metadata)
rb_ufdr_mounter_api_routes = rb_ufdr_mounter_api_routes_get.sync(
    client=client,
    streaming=False,
)
print("ufdr mounter routes", rb_ufdr_mounter_api_routes)
rb_ufdr_mounter_mount_task_schema = rb_ufdr_mounter_mount_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("ufdr mounter mount task schema", rb_ufdr_mounter_mount_task_schema)
rb_ufdr_mounter_mount_post = rb_ufdr_mounter_mount_post.sync(
    client=client,
    streaming=False,
    body=BodyUfdrMounterMountPost(
        inputs=UFDRInputs(
            ufdr_file=FileInput(path=str(Path.cwd() / ".." / "src" / "ufdr-mounter" / "ufdr_mounter" / "testdata" / "test.ufdr")),
            mount_name=TextInput(text="j:"),
        ),
        parameters=UFDRParameters(),
    ),
)
print("ufdr mounter mount response", rb_ufdr_mounter_mount_post)
if isinstance(rb_ufdr_mounter_mount_post, ValidationError):
    print("ufdr mounter mount error ", rb_ufdr_mounter_mount_post)
    sys.exit(1)

sys.exit(0)
####### face match plugin calls ##############

rb_face_match_api_app_metadata  = rb_face_match_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print("face match app_metadata", rb_face_match_api_app_metadata)
rb_face_match_api_routes = rb_face_match_api_routes_get.sync(
    client=client,
    streaming=False,
)
print("face match routes", rb_face_match_api_routes)
rb_face_match_bulkupload_task_schema = rb_face_match_bulkupload_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("face match bulkupload task schema", rb_face_match_bulkupload_task_schema_get)
rb_face_match_bulkupload_post = rb_face_match_bulkupload_post.sync(
    client=client,
    streaming=False,
    body=BodyFaceMatchBulkuploadPost(
        inputs=BulkUploadInputs(
            directory_path=ImageDirectory(path=str(Path.cwd() / ".." / "src" / "face-detection-recognition" / "resources" / "sample_db")),
        ),
        parameters=BulkUploadParameters(
            collection_name="test_collection",
            dropdown_collection_name="test_collection",
        ),
    ),
)
print("face match bulkupload response", rb_face_match_bulkupload_post)

if isinstance(rb_face_match_bulkupload_post, ValidationError):
    print("face match bulkupload error ", rb_face_match_bulkupload_post)
    sys.exit(1)


rb_face_match_findfacebulk_task_schema = rb_face_match_findfacebulk_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("face match find face bulk task schema", rb_face_match_findfacebulk_task_schema)
rb_face_match_findfacebulk_post = rb_face_match_findfacebulk_post.sync(
    client=client,
    streaming=False,
    body=BodyFaceMatchFindfacebulkPost(
        inputs=FindFaceBulkInputs(
            query_directory=DirectoryInput(path=str(Path.cwd() / ".." / "src" / "face-detection-recognition" / "resources")),
        ),
        parameters=FindFaceBulkParameters(
            collection_name="test_collection",
            similarity_threshold=0.5,
        ),
    ),
)
print("face match find face bulk response", rb_face_match_findfacebulk_post)
if isinstance(rb_face_match_findfacebulk_post, ValidationError):
    print("face match find face bulk error ", rb_face_match_findfacebulk_post)
    sys.exit(1)     

if isinstance(rb_deepfake_detection_predict_post, ValidationError):
    print("deepfake detection error ", rb_deepfake_detection_predict_post)
    sys.exit(1)

rb_face_match_deletecollection_task_schema_get = rb_face_match_deletecollection_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("face match delete collection task schema", rb_face_match_deletecollection_task_schema_get)
rb_face_match_deletecollection_post = rb_face_match_deletecollection_post.sync(
    client=client,
    streaming=False,
    body=BodyFaceMatchDeletecollectionPost(
        inputs=DeleteCollectionInputs(),
        parameters=DeleteCollectionParameters(
            collection_name="test_collection",
        ),
    ),
)
print("face match delete collection response", rb_face_match_deletecollection_post)
if isinstance(rb_face_match_deletecollection_post, ValidationError):
    print("face match delete collection error ", rb_face_match_deletecollection_post)
    sys.exit(1)

####### face match plugin calls ##############
rb_deepfake_detection_api_app_metadata = rb_deepfake_detection_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print("deepfake detection app_metadata", rb_deepfake_detection_api_app_metadata)
rb_deepfake_detection_api_routes = rb_deepfake_detection_api_routes_get.sync(
    client=client,
    streaming=False,
)
print("deepfake detection routes", rb_deepfake_detection_api_routes)
rb_deepfake_detection_predict_task_schema = rb_deepfake_detection_predict_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("deepfake detection predict task schema", rb_deepfake_detection_predict_task_schema)
rb_deepfake_detection_predict_post = rb_deepfake_detection_predict_post.sync(
    client=client,
    streaming=False,
    body=BodyDeepfakeDetectionPredictPost(
        inputs=DeepfakeDetectionPredictInputs(
            input_dataset=DirectoryInput(path=str(Path.cwd() / ".." / "src" / "deepfake-detection" / "sample_image")),
            output_file=DirectoryInput(path=str(Path.cwd() / ".." / "src" / "deepfake-detection")),
        ),
        parameters=DeepfakeDetectionPredictParameters(
            facecrop=str(False),
        ),
    ),
)
file_response = rb_deepfake_detection_predict_post.path
print("deepfake detection predict response", file_response)
d_lines = []
if file_response and Path(file_response).exists():
    with open(file_response, "r") as f:
        d_lines.append(f.read())
    print("deepfake detection output file", d_lines)


####### age gender plugin calls ##############

rb_age_gender_api_app_metadata = rb_age_gender_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print("age gender app_metadata", rb_age_gender_api_app_metadata)

rb_age_gender_api_routes = rb_age_gender_api_routes_get.sync(
    client=client,
    streaming=False,
)
print("age gender routes", rb_age_gender_api_routes)


rb_age_gender_predict_task_schema =     rb_age_gender_predict_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("age gender predict task schema", rb_age_gender_predict_task_schema)

age_gender_image_path = Path.cwd() / ".." / "src" / "age_and_gender_detection" / "test_images"

rb_age_gender_predict_post = rb_age_gender_predict_post.sync(
    client=client,
    streaming=False,
    body=BodyAgeGenderPredictPost(
        inputs=AgeGenderPredictInputs(
            image_directory=ImageDirectory(path=str(age_gender_image_path)),
        ),
    ),
)
print("age gender predict response", rb_age_gender_predict_post)

####### audio plugin calls ##############

rb_audio_api_app_metadata = rb_audio_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print("audio app_metadata", rb_audio_api_app_metadata)

rb_audio_api_routes = rb_audio_api_routes_get.sync(
    client=client,
    streaming=False,
)
print("audio routes", rb_audio_api_routes)

rb_audio_transcribe_task_schema = rb_audio_transcribe_task_schema_get.sync(
    client=client,
    streaming=False,
)
print("audio schema", rb_audio_transcribe_task_schema)

## transcribe audio files in a directory ##
audio_text_out_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary"
try:
    bad_path = Path.cwd()
    good_path = Path.cwd() / ".." / "src" / "audio-transcription" / "tests"

    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=BodyAudioTranscribePost(
            inputs=AudioInput(
                input_dir=AudioDirectory(path=str(good_path)),
            ),
        ),
    )
    if isinstance(transcribe_out, ValidationError):
        print("audio transcribe error ", transcribe_out)
    if isinstance(transcribe_out, BatchTextResponse) and len(transcribe_out.texts) > 0:
        data = transcribe_out.texts[0].value
        print("audio transcribe output text ", data)
        audio_text_out_path.mkdir(parents=True, exist_ok=True)
        with open(audio_text_out_path / "audio.txt", "w") as f:
            f.write(data)
        print(f"text summarization output written to file {audio_text_out_path / 'audio.txt'}")    
    else:
        raise Exception(f"audio transcribe failed {transcribe_out}")
except Exception as e:
    print("audio transcribe error", e)
    sys.exit(1)

print("")
print("")
############## text summarization plugin calls ##############

rb_text_summarization_api_app_metadata = rb_text_summarization_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print(
    "text summarization app_metadata",
    rb_text_summarization_api_app_metadata,
)
rb_text_summarization_api_routes = rb_text_summarization_api_routes_get.sync(
    client=client,
    streaming=False,
)
print(
    "text summarization routes",
    rb_text_summarization_api_routes,
)
rb_text_summarization_task_schema = rb_text_summarization_summarize_task_schema_get.sync(
    client=client,
    streaming=False,
)
print(
    "text summarization schema",
    rb_text_summarization_task_schema,
)

## summarize text files in a directory using ollama model ##
# input_dir is a test input directory with text files
# the output will be written to a text file in the output_dir directory
try:
    #text_path = Path.cwd() / ".." / "src" / "text-summary" / "test_input"
    summarize_text_in_path = audio_text_out_path

    summarize_text_out_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary_output"
    summarize_text_out_path.mkdir(parents=True, exist_ok=True)
    text_summarization_out = rb_text_summarization_summarize_post.sync(
        client=client,
        streaming=False,
        body=BodyTextSummarizationSummarizePost(
            inputs=TextSummarizationSummarizeInputs(
                input_dir=DirectoryInput(path=str(summarize_text_in_path)),
                output_dir=DirectoryInput(path=str(summarize_text_out_path)),
            ),
            parameters=TextSummarizationSummarizeParameters(
                model="llama3.2:3b",
            ),
        ),
    )

    if isinstance(text_summarization_out, ValidationError):
        print("text summarization error ", text_summarization_out)
    if isinstance(text_summarization_out, BatchTextResponse) and len(text_summarization_out.texts) > 0:
        data = text_summarization_out.texts[0].value
        print("text summarization output text ", data)

except Exception as e:
    print("text summarization error", e)
