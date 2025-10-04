# API Client Generation Guide

The `rescue-box-api-client` is a critical dependency for the pipeline system. It is a Python package containing a type-safe API client that is auto-generated from the RescueBox backend's OpenAPI specification.

**Purpose:**

*   It provides a clean, programmatic way for Celery tasks in `rb_celery.py` to communicate with the various plugin API endpoints (e.g., `/audio/transcribe`, `/text_summarization/summarize`).
*   It ensures that the data models (for both requests and responses) used in the pipeline tasks are consistent with the models defined in the backend services, reducing runtime errors.

**Generation Process:**

The client is not written manually. It is generated using the `openapi-python-client` tool. The process is as follows:

1.  **Start the RescueBox Backend**: The main FastAPI application (`rb-api`) must be running.
2.  **Fetch OpenAPI Schema**: The `openapi.json` file, which describes the entire API, is fetched from the running server.
    ```bash
    curl --header "Content-Type: application/json" "http://localhost:8000/openapi.json" > openapi.json
    ```
3.  **Generate Client**: The `openapi-python-client` tool is used to generate the Python client code from the schema file.
    ```bash
    # Example command
    openapi-python-client generate --path openapi.json --output-path src/rescue-box-api-client --overwrite
    ```
This process needs to be repeated whenever there are changes to the backend API endpoints or their data models to keep the client in sync.