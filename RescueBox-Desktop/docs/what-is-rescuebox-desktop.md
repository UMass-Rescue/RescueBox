# Problem Statement

Public institutions and investigators find it difficult to employ ML in their workflows. They cannot use cloud technologies as the material they handle is sensitive. They resort to manually cloning different open-source repositories, installing requirements, manually specifying inputs, and observing outputs on the file system, a difficult and error-prone process that is suited only to the most tech-savvy investigators. On the flip side, those who do not have technical experience buy tools that are expensive.

RescueBox Desktop (RBox) aims to be a self-contained binary that’s a library of models. In this application, users simply specify the model they want to run (selected from a list of available models), specify its inputs and analyze outputs when ready. RBox handles the rest: running the jobs, and interfacing with different ML models. As of v0.1.0, the models need to be running in the background adhering to the [FlaskML](https://github.com/UMass-Rescue/Flask-ML) interface.

# Stakeholders

We see three stakeholders:

1. Users: Investigators, and researchers
    - Want a user-friendly experience
    - Just want to get the job done
    - Want to see visual results
2. Model Developers
    - Want to focus on building great models
    - But, also need to work a little on exposing them to their users
3. Frontend Developers (us!)
    - Want to make UI extensible: it should be easy to add more models to the project
    - Low maintenance effort
    - Provide separation of concerns: we are just a desktop app frontend
