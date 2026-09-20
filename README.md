# RescueBox is a AI/ML digital-forensics application. 

It is intended for investigators who have a directory of evidence—images, audio, PDFs, text files, and want to run AI/ML analysis. 

This is done local without uploading that evidence to a cloud service.

## Sample forensics analysis:

“Transcribe every audio recording in this directory.”

“Find photographs matching ‘a person wearing a red jacket.’”

“Find other images from the same event as this photo.”

“Describe these images, then search their descriptions.”

“Find faces resembling the supplied query photographs.”

“Estimate the age range and gender presentation of detected faces.”

“Flag images that may be manipulated or AI-generated.”

“Summarize all PDFs in this evidence folder.”


## The workflow is:

Create or load an investigative case.

Select an analysis plugin—or describe the desired analysis to the assistant.

Point RescueBox at a local evidence directory. fill in or select ML parameters like model to use,top-k.

Submit a job.

Inspect the results and job history.

Optionally chain several tools into a pipeline.

## Implementation Details:

Frontend: A Python/NiceGUI web application served locally, normally at localhost:8080. It manages cases, chat history, forms, jobs, and result displays.

Assistant: A locally hosted small AI model through Ollama converts natural-language requests into structured plugin calls. It is a tool selector and pipeline planner.

Backend: FastAPI dynamically exposes the commands defined by the plugin packages as HTTP routes.

Plugins: Mostly independent Python packages, each containing its own input schema and analysis implementation.

Storage: SQLite stores UI data such as cases, conversations, and job history. PostgreSQL with pgvector stores semantic image/text embeddings.

## Deployment and demo usage

Windows installer is available ,details in INSTALL.md.  Developer mac install is also available

After Installing rescuebox refer the Resources -> Readme for plugin details and Demo link for a walk thru.

## Useful links

 - [Wiki](https://github.com/UMass-Rescue/RescueBox/wiki) for developers

 - [Previous Release](https://github.com/UMass-Rescue/RescueBox/blob/V2.1.0/README.md) for end-users

 - [web site](https://rescue-lab.org) for more on Rescue Lab


<img  width="200px" src="https://images.squarespace-cdn.com/content/v1/5efb7aa577f8b34b0f786c0f/1598361988326-7EWAXEOBNQGIQGSQK8PS/Rescue+Lab+LogoOL.jpg?format=1500w">
