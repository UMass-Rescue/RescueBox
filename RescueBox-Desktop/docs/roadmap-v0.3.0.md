# Roadmap for v0.3.0

## UI Functional Requirements

1. Add validation for Run page (all the input fields types)
2. Add logic to form Request Body (FormData -> RequestBody) - write a model or class (form should use keys based on input schema)
3. Tabs for ModelRunTask page on the left (see https://github.com/settings/profile)
4. Job Details: model title, task used, start time, end time, completed, RequestBody (switch case to show the request body used, refactor current input_fields, parameter_fields to make them displayable), raw ResponseBody under a button (Show Raw ResponseBody)
5. Outputs: create a component under src/renderer/components/response_body for each response type
  - FileResponse
  - DirectoryResponse
  - MarkdownResponse
  - TextResponse
  - BatchFileResponse
  - BatchTextResponse
  - BatchDirectoryResponse

# FileResponse

Use preview components from below

# DirectoryResponse

- List of files in the directory with search and Browse button

# MarkdownResponse

- Use markdown component/preview component from below

# BatchFileResponse

Global Search

Image DROPDOWN->
  Image Search
  Image Grid (in each card, with preview, open, copy)

Video DROPDOWN->
  Video Search
  Video Grid (in each card, with preview, open, copy)

Audio DROPDOWN->
  Audio Search
  Audio Grid (in each card, with preview, open, copy)

CSV DROPDOWN->
  CSV Search
  CSV Grid (in each card, with preview, open, copy)

Text DROPDOWN->
  Text Search
  Text grid

JSON DROPDOWN paragraph tags, look into JSON renderer ->
  JSON Search
  JSON grid

MARKDOWN DROPDOWN ->
  Markdown Search
  Markdown grid

# BatchTextResponse

GRID->
  Text Search
  Text

# BatchDirectoryResponse

- use the same component as DirectoryResponse

## Backend Requirements

1. Figure out (modelUid, taskid) bundling. The frontend and backend should share (modelUid, taskid) for all inference related jobs
2. Delete and refactor calling services, getting responses, snakeCase conversion
3. Delete models table, figure out uniquely identifying models when models can come and go
  - id = hash(model_name + response_body of /api/routes)

## Combined Requirements

1. FlaskML change
2. Store markdown in backend DB
3. Displaying info page markdown in frontend (when both model is online and offline)

## General Requirements

Allow MB4 to go back
Allow MB3 to go forward
