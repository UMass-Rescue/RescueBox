"""Contains all the data models used in inputs/outputs"""

from .age_gender_predict_inputs import AgeGenderPredictInputs
from .audio_directory import AudioDirectory
from .audio_input import AudioInput
from .batch_directory_response import BatchDirectoryResponse
from .batch_file_response import BatchFileResponse
from .batch_text_response import BatchTextResponse
from .body_age_gender_predict_post import BodyAgeGenderPredictPost
from .body_audio_transcribe_post import BodyAudioTranscribePost
from .body_deepfake_detection_predict_post import BodyDeepfakeDetectionPredictPost
from .body_face_match_bulkupload_post import BodyFaceMatchBulkuploadPost
from .body_face_match_deletecollection_post import BodyFaceMatchDeletecollectionPost
from .body_face_match_findfacebulk_post import BodyFaceMatchFindfacebulkPost
from .body_text_summarization_summarize_post import BodyTextSummarizationSummarizePost
from .body_ufdr_mounter_mount_post import BodyUfdrMounterMountPost
from .bulk_upload_inputs import BulkUploadInputs
from .bulk_upload_parameters import BulkUploadParameters
from .deepfake_detection_predict_inputs import DeepfakeDetectionPredictInputs
from .deepfake_detection_predict_parameters import DeepfakeDetectionPredictParameters
from .delete_collection_inputs import DeleteCollectionInputs
from .delete_collection_parameters import DeleteCollectionParameters
from .directory_input import DirectoryInput
from .directory_response import DirectoryResponse
from .file_input import FileInput
from .file_response import FileResponse
from .file_type import FileType
from .find_face_bulk_inputs import FindFaceBulkInputs
from .find_face_bulk_parameters import FindFaceBulkParameters
from .http_validation_error import HTTPValidationError
from .image_directory import ImageDirectory
from .markdown_response import MarkdownResponse
from .text_input import TextInput
from .text_response import TextResponse
from .text_summarization_summarize_inputs import TextSummarizationSummarizeInputs
from .text_summarization_summarize_parameters import TextSummarizationSummarizeParameters
from .ufdr_inputs import UFDRInputs
from .ufdr_parameters import UFDRParameters
from .validation_error import ValidationError

__all__ = (
    "AgeGenderPredictInputs",
    "AudioDirectory",
    "AudioInput",
    "BatchDirectoryResponse",
    "BatchFileResponse",
    "BatchTextResponse",
    "BodyAgeGenderPredictPost",
    "BodyAudioTranscribePost",
    "BodyDeepfakeDetectionPredictPost",
    "BodyFaceMatchBulkuploadPost",
    "BodyFaceMatchDeletecollectionPost",
    "BodyFaceMatchFindfacebulkPost",
    "BodyTextSummarizationSummarizePost",
    "BodyUfdrMounterMountPost",
    "BulkUploadInputs",
    "BulkUploadParameters",
    "DeepfakeDetectionPredictInputs",
    "DeepfakeDetectionPredictParameters",
    "DeleteCollectionInputs",
    "DeleteCollectionParameters",
    "DirectoryInput",
    "DirectoryResponse",
    "FileInput",
    "FileResponse",
    "FileType",
    "FindFaceBulkInputs",
    "FindFaceBulkParameters",
    "HTTPValidationError",
    "ImageDirectory",
    "MarkdownResponse",
    "TextInput",
    "TextResponse",
    "TextSummarizationSummarizeInputs",
    "TextSummarizationSummarizeParameters",
    "UFDRInputs",
    "UFDRParameters",
    "ValidationError",
)
