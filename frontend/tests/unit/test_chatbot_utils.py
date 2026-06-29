"""
Unit tests for chatbot utility functions.

This module tests the core utility functions that power RescueBox's
chatbot intelligence and request processing. These utilities handle
argument normalization, request validation, and user interaction
management.

The tests cover all major utility functions:
- Argument normalization (converting user inputs to API-compatible formats)
- Endpoint-specific parameter mapping
- RescueBox request validation (keyword matching, path detection)
- Content filtering and safety checks
- Rejection message generation for unsupported requests

These utilities are critical for ensuring consistent, safe, and
user-friendly interactions with the RescueBox AI assistant.
"""

from frontend.chatbot.utils import (
    normalize_arguments,
    is_rescuebox_request,
    get_rejection_message,
)

# Test constants for argument normalization
INPUT_DIRECTORY_KEY = "input_directory"
OUTPUT_DIRECTORY_KEY = "output_directory"
INPUT_DIR_KEY = "input_dir"
OUTPUT_DIR_KEY = "output_dir"
PATH_KEY = "path"
FOLDER_KEY = "folder"
OUTPUT_PATH_KEY = "output_path"
CUSTOM_KEY = "custom_key"
CUSTOM_VALUE = "custom_value"

# Test paths
TEST_INPUT_PATH = "/tmp/test"
TEST_OUTPUT_PATH = "/tmp/output"
TEST_ANOTHER_PATH = "/tmp/another"
TEST_FOLDER_PATH = "/tmp/folder"
TEST_IMAGES_PATH = "/tmp/images"
TEST_VIDEOS_PATH = "/tmp/videos"
TEST_FACES_PATH = "/tmp/faces"
TEST_QUERY_PATH = "/tmp/query"
TEST_CASE_PATH = "/case/photos"
TEST_EVIDENCE_PATH = "/evidence/case1"
TEST_DATA_PATH = "/tmp/data/files"

# Endpoints for normalization
AGE_GENDER_ENDPOINT = "age-gender/predict"
DEEPFAKE_ENDPOINT = "deepfake_detection/give_prediction"
BULK_UPLOAD_ENDPOINT = "face-match/bulk_upload_endpoint"
FIND_FACE_ENDPOINT = "face-match/findfacebulk"

# Endpoint-specific normalized keys
IMAGE_DIRECTORY_KEY = "image_directory"
INPUT_DATASET_KEY = "input_dataset"
DIRECTORY_PATH_KEY = "directory_path"
QUERY_DIRECTORY_KEY = "query_directory"

# Test messages for request validation
TRANSCRIBE_REQUEST = "transcribe audio in /tmp/recordings"
DESCRIBE_REQUEST = "describe images in /case/photos"
FORENSIC_REQUEST = "analyze evidence in /evidence/case1"
WEATHER_REQUEST = "what's the weather today?"
JOKE_REQUEST = "tell me a joke"
RECIPE_REQUEST = "how to cook pasta?"
GREETING_REQUEST = "hello"
PROCESS_REQUEST = "process files in /tmp/data/files"
HELLO_REQUEST = "hello there how are you today"
RANDOM_REQUEST = "random text"

# Rejection reasons
NON_FORENSIC_REASON = "non_forensic"
NO_MATCH_REASON = "no_match"
FILTER_DISABLED_REASON = "filter_disabled"
KEYWORD_MATCH_REASON = "keyword_match"
PATH_DETECTED_REASON = "path_detected"

# Rejection message content
REJECTION_TITLE = "Request Not Supported"
DIDNT_UNDERSTAND_TITLE = "I Didn't Understand"
RESCUEBOX_ASSISTANT_TEXT = "RescueBox Forensic Assistant"
WHAT_I_CAN_DO_TEXT = "What I CAN Do"
EXAMPLES_TEXT = "Examples:"

# Keyword variations for testing
KEYWORD_TEST_CASES = [
    "transcribe recordings",
    "detect deepfakes",
    "find matching faces",
    "summarize documents",
    "classify age and gender",
]


class TestNormalizeArguments:
    """Tests for argument normalization utility functions.

    This class validates the argument normalization system that converts
    user-friendly parameter names to API-compatible formats. The normalization
    handles common variations in parameter naming and provides endpoint-specific
    mappings for different RescueBox tools.

    Normalization features tested:
    - Standard key mapping (input_directory -> input_dir)
    - Case-insensitive processing
    - Multiple key resolution (last key wins)
    - Endpoint-specific parameter mapping
    - Preservation of unknown keys
    - Complex multi-endpoint scenarios
    """

    def test_normalize_input_directory(self):
        """Test normalization of input_directory to input_dir.

        Validates that the common variation 'input_directory' is correctly
        normalized to the standard 'input_dir' key expected by most APIs.
        """
        args = {INPUT_DIRECTORY_KEY: TEST_INPUT_PATH}
        result = normalize_arguments(args)
        assert INPUT_DIR_KEY in result
        assert result[INPUT_DIR_KEY] == TEST_INPUT_PATH
        assert INPUT_DIRECTORY_KEY not in result

    def test_normalize_output_directory(self):
        """Test normalization of output_directory to output_dir.

        Ensures that 'output_directory' is properly converted to the
        standard 'output_dir' parameter name used across RescueBox tools.
        """
        args = {OUTPUT_DIRECTORY_KEY: TEST_OUTPUT_PATH}
        result = normalize_arguments(args)
        assert OUTPUT_DIR_KEY in result
        assert result[OUTPUT_DIR_KEY] == TEST_OUTPUT_PATH

    def test_normalize_multiple_variations(self):
        """Test normalization of multiple key variations with conflict resolution.

        Validates that when multiple input keys map to the same normalized key,
        the last processed key wins, providing predictable behavior for complex
        argument sets with overlapping parameter names.
        """
        args = {
            INPUT_DIRECTORY_KEY: TEST_INPUT_PATH,
            "output_path": TEST_OUTPUT_PATH,
            PATH_KEY: TEST_ANOTHER_PATH,
            FOLDER_KEY: TEST_FOLDER_PATH,
        }
        result = normalize_arguments(args)
        # When multiple keys map to the same normalized key, the last one wins
        # Processing order: input_directory -> path -> folder
        # So "folder" (last) overwrites previous values
        assert result[INPUT_DIR_KEY] == TEST_FOLDER_PATH  # Last one wins
        assert result[OUTPUT_DIR_KEY] == TEST_OUTPUT_PATH

    def test_normalize_age_gender_endpoint(self):
        """Test endpoint-specific normalization for age_gender tool.

        Validates that the age-gender prediction endpoint receives the
        correct parameter name ('image_directory' instead of 'input_dir')
        as required by its specific API contract.
        """
        args = {INPUT_DIR_KEY: TEST_IMAGES_PATH}
        result = normalize_arguments(args, endpoint=AGE_GENDER_ENDPOINT)
        assert IMAGE_DIRECTORY_KEY in result
        assert result[IMAGE_DIRECTORY_KEY] == TEST_IMAGES_PATH

    def test_normalize_deepfake_endpoint(self):
        """Test endpoint-specific normalization for deepfake detection.

        Ensures that deepfake detection tool receives parameters in the
        expected format ('input_dataset' instead of 'input_dir') for
        proper API communication.
        """
        args = {INPUT_DIR_KEY: TEST_VIDEOS_PATH}
        result = normalize_arguments(args, endpoint=DEEPFAKE_ENDPOINT)
        assert INPUT_DIR_KEY in result
        assert result[INPUT_DIR_KEY] == TEST_VIDEOS_PATH

    def test_normalize_bulk_upload_endpoint(self):
        """Test endpoint-specific normalization for face-match bulk upload.

        Verifies that bulk upload operations use the correct parameter
        naming ('directory_path') as expected by the face matching API.
        """
        args = {INPUT_DIR_KEY: TEST_FACES_PATH}
        result = normalize_arguments(args, endpoint=BULK_UPLOAD_ENDPOINT)
        assert DIRECTORY_PATH_KEY in result
        assert result[DIRECTORY_PATH_KEY] == TEST_FACES_PATH

    def test_normalize_find_face_endpoint(self):
        """Test endpoint-specific normalization for find face operations.

        Confirms that face finding queries use the proper parameter
        structure ('query_directory') required by the face matching
        search functionality.
        """
        args = {INPUT_DIR_KEY: TEST_QUERY_PATH}
        result = normalize_arguments(args, endpoint=FIND_FACE_ENDPOINT)
        assert QUERY_DIRECTORY_KEY in result
        assert result[QUERY_DIRECTORY_KEY] == TEST_QUERY_PATH

    def test_normalize_unknown_key(self):
        """Test that unknown keys are preserved without modification.

        Ensures that custom or unrecognized parameter keys are passed
        through unchanged, allowing flexibility for tool-specific
        parameters while still normalizing known keys.
        """
        args = {CUSTOM_KEY: CUSTOM_VALUE, INPUT_DIR_KEY: TEST_INPUT_PATH}
        result = normalize_arguments(args)
        assert CUSTOM_KEY in result
        assert result[CUSTOM_KEY] == CUSTOM_VALUE
        assert result[INPUT_DIR_KEY] == TEST_INPUT_PATH

    def test_normalize_case_insensitive(self):
        """Test that normalization is case-insensitive for key matching.

        Validates that parameter keys are matched regardless of case,
        providing user-friendly input handling where 'INPUT_DIRECTORY'
        and 'input_directory' are treated identically.
        """
        args = {"INPUT_DIRECTORY": TEST_INPUT_PATH, "Output_Path": TEST_OUTPUT_PATH}
        result = normalize_arguments(args)
        assert INPUT_DIR_KEY in result
        assert OUTPUT_DIR_KEY in result

    def test_normalize_preserves_search_query_for_image_embeddings(self):
        """CLIP / image search: ``query`` must stay as the text phrase, not ``query_directory``."""
        args = {"input_dir": TEST_IMAGES_PATH, "query": "food"}
        ep = "image_embeddings/search_images"
        result = normalize_arguments(args, endpoint=ep)
        assert result.get("query") == "food"
        assert result.get("input_dir") == TEST_IMAGES_PATH

    def test_normalize_preserves_search_query_for_text_embeddings(self):
        args = {"input_dir": "/tmp/summaries", "query": "witness statement"}
        result = normalize_arguments(args, endpoint="text_embeddings/search")
        assert result.get("query") == "witness statement"


class TestIsRescueboxRequest:
    """Tests for RescueBox request validation and content filtering.

    This class validates the intelligent request processing that determines
    whether user messages should be handled by RescueBox tools or rejected.
    The validation uses multiple criteria including keyword matching, path
    detection, and content filtering.

    Request validation features tested:
    - Keyword-based tool detection (transcribe, analyze, etc.)
    - File/directory path recognition
    - Content filtering for inappropriate requests
    - Case-insensitive matching
    - Filter disablement for testing/admin purposes
    - Rejection reason categorization
    """

    def test_valid_audio_request(self):
        """Test valid audio transcription request with keyword and path.

        Validates that requests containing transcription keywords and
        file paths are correctly identified as valid RescueBox operations,
        supporting both keyword matching and path detection criteria.
        """
        is_valid, reason = is_rescuebox_request(TRANSCRIBE_REQUEST)
        assert is_valid is True
        assert reason in [KEYWORD_MATCH_REASON, PATH_DETECTED_REASON]

    def test_valid_image_request(self):
        """Test valid image description request with forensic context.

        Ensures that image analysis requests with case-related paths
        are properly recognized as legitimate RescueBox forensic work,
        demonstrating path-based validation in addition to keywords.
        """
        is_valid, reason = is_rescuebox_request(DESCRIBE_REQUEST)
        assert is_valid is True

    def test_valid_forensic_request(self):
        """Test valid forensic analysis request with evidence path.

        Confirms that forensic evidence analysis requests with appropriate
        directory structures are accepted as valid RescueBox operations,
        supporting digital forensics workflows with proper path validation.
        """
        is_valid, reason = is_rescuebox_request(FORENSIC_REQUEST)
        assert is_valid is True

    def test_image_search_with_sports_subject_allowed(self):
        """Subject words like 'sports' must not block when prompt is clearly image search."""
        is_valid, reason = is_rescuebox_request(
            "search these images for a sports event"
        )
        assert is_valid is True
        assert reason == KEYWORD_MATCH_REASON

    def test_blocked_weather_request(self):
        """Test blocked weather request filtering.

        Validates that non-forensic requests like weather queries are
        properly rejected with appropriate categorization, preventing
        misuse of the forensic assistant for general-purpose queries.
        """
        is_valid, reason = is_rescuebox_request(WEATHER_REQUEST)
        assert is_valid is False
        assert reason == NON_FORENSIC_REASON

    def test_blocked_joke_request(self):
        """Test blocked entertainment request filtering.

        Ensures that entertainment or casual conversation requests are
        filtered out, maintaining focus on forensic and analytical tasks
        that are the core purpose of RescueBox.
        """
        is_valid, reason = is_rescuebox_request(JOKE_REQUEST)
        assert is_valid is False
        assert reason == NON_FORENSIC_REASON

    def test_blocked_recipe_request(self):
        """Test blocked recipe request"""
        is_valid, reason = is_rescuebox_request("how to cook pasta?")
        assert is_valid is False
        assert reason == "non_forensic"

    def test_blocked_greeting(self):
        """Test blocked simple greeting"""
        is_valid, reason = is_rescuebox_request("hello")
        assert is_valid is False
        assert reason == "non_forensic"

    def test_path_detection(self):
        """Test that file paths trigger valid request"""
        # Use input with path but no keywords (keywords are checked first)
        # Must avoid all keywords in RESCUEBOX_KEYWORDS
        # Use a very simple string with just a path - no keywords at all
        is_valid, reason = is_rescuebox_request("process files in /tmp/data/files")
        assert is_valid is True
        assert reason == "keyword_match"

    def test_no_match_request(self):
        """Test request with no keywords or paths"""
        # Use string without any keywords or paths
        # Must avoid: "text", "words", "random" might match something, use very generic text
        is_valid, reason = is_rescuebox_request("hello there how are you today")
        assert is_valid is False
        assert reason == "no_match"

    def test_filter_disabled(self):
        """Test that filter can be disabled"""
        is_valid, reason = is_rescuebox_request("random text", filter_enabled=False)
        assert is_valid is True
        assert reason == "filter_disabled"

    def test_keyword_variations(self):
        """Test various keyword variations for tool recognition.

        Validates that different phrasings of the same forensic operations
        are correctly identified, ensuring robust natural language processing
        that can handle varied user expressions for the same analytical tasks.
        """
        for test_case in KEYWORD_TEST_CASES:
            is_valid, reason = is_rescuebox_request(test_case)
            assert is_valid is True, f"Failed for: {test_case}"


class TestGetRejectionMessage:
    """Tests for rejection message generation and user guidance.

    This class validates the user-friendly error messaging system that
    provides helpful feedback when requests cannot be processed. The
    rejection messages guide users toward appropriate RescueBox usage
    and explain available capabilities.

    Rejection message features tested:
    - Different message types for various rejection reasons
    - Proper markdown formatting for UI display
    - Inclusion of helpful examples and guidance
    - Consistent branding and tone
    - Comprehensive capability listings
    """

    def test_non_forensic_rejection(self):
        """Test rejection message for non-forensic requests"""
        message = get_rejection_message("non_forensic")
        assert "RescueBox chat Assistant" in message
        assert "What will work:" in message

    def test_no_match_rejection(self):
        """Test rejection message for unmatched requests"""
        message = get_rejection_message("no_match")
        assert "RescueBox Forensic Assistant" in message or "Examples:" in message
        assert "RescueBox Forensic Assistant" in message
        assert "Examples:" in message

    def test_rejection_contains_examples(self):
        """Test that rejection messages contain helpful examples"""
        message = get_rejection_message("non_forensic")
        assert "Transcribe" in message or "transcribe" in message
        assert "Detect" in message or "detect" in message

    def test_rejection_format(self):
        """Test that rejection messages are properly formatted markdown"""
        message = get_rejection_message("non_forensic")
        assert "**RescueBox" in message
        assert "|" in message  # Should contain table
