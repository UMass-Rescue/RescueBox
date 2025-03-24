# Roadmap for v0.1.0

## UI Functional Requirements:

See [ui-rbox-desktop-v0.1.0.pdf](./ui-rbox-desktop-v0.1.0.pdf)

1. Model pages: 
    1. View all available models
        - Show if a model is able to be run (based on model registration)
    2. Register model IP addresses
        - To be able to associate a model app to the IP address its server is running on

2. Sample Model App Pages (specific model apps)
    1. View a specific model’s details 
        - UID
        - Name
        - Version
        - Authors
        - Last Updated
        - Input Type(s) 
        - Output Type(s) 
        - Parameters
        - Constraints
    2. Run model
        - Collects - inputs (browse files for input), outputs (browse to choose an output directory), and model parameters -> a form to add values.
    3. Outputs page (under Jobs)
        - Tailored to the specific model (ex: gallery for image model app)      

2. Jobs pages:
    1. Active/Past Jobs page
        - Current running jobs with a cancel button
        - View job button -> open up following page
        - Completed jobs (history of jobs)
    2. Job Details page (two tabs)
        - Details tab
            - UID
            - Start/end date/time
            - Status (In progress, completed, canceled, failed)
            - Inputs used
            - Outputs selected
            - A log output with any messages received from the server
            - Model used (with an inspect button that links to the original model page)
        - Outputs tab (defined above under "Sample Model App Pages")

# Development Plan

## Frontend

1. Starter code
2. TailwindCSS
3. Navigation bar
4. Model management pages (includes model list and registration)
5. Sample model app pages (includes description, run job, outputs tab)
6. Jobs pages (includes job list, and job details)

## Backend

- Persistence
    - Tables for models, jobs and model registration (mapping from model to IP address)
    - Providing an API so that backend can access the data
    - Use an ORM
- Model Registration
    - Store the IP address when received
    - Poll the server to see if its running/not available
- Jobs
    - Expose a standard API for specific model app pages to start a job (after clicking the "Run Model" button)
    - Call the appropriate FlaskML endpoint to start the job
    - When FlaskML response completes (with failed, or success), store in DB, and report back to frontend
- Outputs
    - Expose a standard API to get access to job metadata
- CI
    - Setup github actions to build executables for all 3 OS platforms
    - Upload artifacts to assets
- Logging
    - Standard process to log

## General Tasks

- Write a README.md
    - Include [What is RescueBox Desktop?](./what-is-rescuebox-desktop.md)
    - Include [this roadmap](./roadmap-v0.1.0.md)
    - Include docs for development
- Upload latest architecture design to docs
- Setup a testing framework?
