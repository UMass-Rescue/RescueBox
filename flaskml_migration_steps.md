### Steps to integrate Flask-ML projects into RescueBox

1. Fork https://github.com/UMass-Rescue/RescueBox into your own repository.
2. Clone your forked repository to your local machine.
```
git clone git@github.com:<your_username>/RescueBox.git
```
3. Create a new branch for your Flask-ML project.
```
git checkout -b <branch_name>
```
4. Copy your Flask-ML based project into the `src` directory.
```
cp -r <path_to_flask_ml_project> src/
```
5. Remove git related files from the new directory (src/project) created in the previous step.
```
rm -rf src/<project_dir>/.git
rm src/<project_dir>/.gitignore
```
6. Convert your project to use poetry for dependency management. https://python-poetry.org/docs/basic-usage/
7. Include your project as a dependency in the root level `pyproject.toml` file.
```
# Add this to the [tool.poetry.dependencies] section
project-name = {path = "src/project-name", develop = true}
```
8. Install the dependencies for the entire project. Go to the root directory of the project and run:
```
poetry install
```
9. (Optional) Modify the dependencies in your projects `pyproject.toml` file until poetry can successfully install all dependencies. Refer to src/rb-audio-transcription/pyproject.toml for an example.
10. IMPORTANT: Submit your Pull Request (PR) for an initial review at this point (send the PR to Prasanna on Slack). List the libraries and the models being used, along with their license information as a comment in the PR. This is to ensure that the libraries and models being used are compatible with the RescueBox project. The team will review your PR and provide feedback. You can continue with the migration steps while waiting for the initial review.
11. Transition from Flask-ML to RescueBox API. Inside the file that runs your server (or wherever you have your FlaskML app instance), do the following:
  * Replace `from flask_ml.flask_ml_server.models import ...` with `from rb.api.models import ...`.
  * Replace `flask_ml.flask_ml_server import MLServer` with `from rb.lib.ml_service import MLService`.
  * Add APP_NAME=`your-app-name` to the server file. Example: `APP_NAME = "audio-transcription"`.
  * Replace `MLServer(__init__)` with `MLService(APP_NAME)`.
  * Remove the `@server.route` decorator from the machine learning functions being decorated.
  * Define new functions:
    * cli_parser - takes in a list of arguments (passing in through the cli) and returns the input (first parameter to your ML function) to the ML function.
    * param_parser (OPTIONAL - only if you have parameters to your ML function) - takes in a list of arguments (passing in through the cli) and returns the parameters (second parameter to your ML function) to the ML function.
  * Call the `add_ml_service` function with the required parameters for each ML endpoint in your application. Example:
```python
import typer

...

server.add_ml_service(
    rule="/summarize",
    ml_function=summarize,
    inputs_cli_parser=typer.Argument(parser=inputs_cli_parse, help="Input and output directory paths"),
    parameters_cli_parser=typer.Argument(parser=parameters_cli_parse, help="Model to use for summarization"),
    short_title="Text Summarization",
    order=0,
    task_schema_func=task_schema,
)
### NOTE: You will get a `RuntimeError: Type not yet supported: <class '__main__.Inputs'>` error if you don't use typer.Argument(parse=inputs_cli_parser, ...) in the `add_ml_service` function.
```
12. Define `app = ml_service_object.app` in your server file. This is the Typer app that will be used to run the CLI commands and to generate the API endpoints.
13. Replace `server.run()` with `app()` within `if __name__ == "__main__":`. This will run the Typer app.
14. In `rescuebox/plugins/__init__.py`, add your app to the list of `plugins`. Example:
```python
from text_summary.main import app as text_summary_app, APP_NAME as text_summary_app_name

# Adding the following to the list of plugins in the "plugins" variable
RescueBoxPlugin(text_summary_app, text_summary_app_name, "Text summarization library"),
```
15. Test your typer app manually. Go to the root directory of the project and run:
```
poetry run python src/<project_dir>/file_with_typer_app.py --help  # prints all available commands

# Test all commands. Examples from Text Summarization
poetry run python src/text-summary/text_summary/main.py /text_summarization/summarize "src/text-summary/example_files,./out" gemma3:1b

poetry run python src/text-summary/text_summary/main.py /text_summarization/api/app_metadata

poetry run python src/text-summary/text_summary/main.py /text_summarization/api/routes

poetry run python src/text-summary/text_summary/main.py /text_summarization/summarize/payload_schema

poetry run python src/text-summary/text_summary/main.py /text_summarization/summarize/sample_payload

poetry run python src/text-summary/text_summary/main.py /text_summarization/summarize/task_schema
```
16. Add tests for your app in src/<project_dir>/tests. You can use the tests in src/audio-transcription/tests as a reference. Extend the rb.lib.common_tests.RBAppTest class to test your app. RBAppTest automatically tests the routes, app metadata, and task schema in both the command line and the API. Add additional tests to test the ML service in your app. Refer to the following files for examples to learn from:
```
src/audio-transcription/tests/test_main.py
src/text-summary/tests/test_main_text_summary.py
src/age_and_gender_detection/tests/test_main_age_gender.py
```
17. Make sure all the tests pass and the Github Actions workflow is successful. Refer to .github/workflows/ for the workflow files.
18. Send your pull request for review. Someone from the team will review your code and provide feedback. The PR requires at least one approval from a team member before it can be merged.