# RescueBox Project Context

This document provides context for the RescueBox project for the Gemini large language model.

## Project Overview

RescueBox is a command-line interface (CLI) application with a plugin-based architecture. It is designed to be extensible, allowing for the addition of new functionalities through plugins. The core of the application is built with Python, utilizing the `typer` library to create a user-friendly and powerful command-line experience.

## Technical Details

*   **Programming Language:** Python
*   **CLI Framework:** `typer`
*   **Package Management:** `poetry`
*   **Main Entry Point:** `rescuebox.main:app`

## Project Structure

The project is organized into several directories, with the main application logic located in the `rescuebox` directory. Plugins are located in the `src` directory, with each plugin in its own subdirectory.

### Key Files

*   `pyproject.toml`: Defines the project's metadata, dependencies, and scripts.
*   `rescuebox/main.py`: The main entry point for the CLI application. This file is responsible for loading the plugins and setting up the `typer` application.
*   `CONTRIBUTING.md`: Provides guidelines for contributing to the project.

## Plugin Architecture

The RescueBox plugin architecture is designed to be modular and extensible, allowing for the seamless integration of new functionalities. Here's a detailed breakdown of how plugins work, how they are exposed, and how their inputs and outputs are validated.

### Plugin Discovery and Loading

Plugins are discovered and loaded into the main application through a straightforward mechanism:

1.  **Plugin Aggregation:** The `rescuebox/plugins/__init__.py` file is responsible for collecting all available plugins. It imports the `typer` app from each plugin's `main.py` file and wraps it in a `RescueBoxPlugin` dataclass, which stores the plugin's `typer` application, its CLI name, and its full name.

2.  **Dynamic Loading:** The main application entry point, `rescuebox/main.py`, imports the list of `RescueBoxPlugin` instances from `rescuebox/plugins/__init__.py`. It then iterates through this list and adds each plugin's `typer` app to the main `typer` application using `app.add_typer()`. This makes the plugin's commands available as subcommands of the main `rescuebox` command.

### Exposing Plugins via API

In addition to being accessible via the CLI, plugin functionalities are also exposed through a FastAPI-based RESTful API. This is achieved as follows:

1.  **Dynamic Route Generation:** The `src/rb-api/rb/api/routes/cli.py` file is the core of the API exposure mechanism. It inspects the `typer` commands registered in the main `rescuebox` application and dynamically generates corresponding FastAPI endpoints for each command.

2.  **Command Handling:** The `command_callback` function in `cli.py` wraps the original `typer` command's callback function. This wrapper handles both synchronous and streaming responses, allowing for flexible data handling. For streaming responses, the output is sent as a series of server-sent events (SSE).

3.  **API Router:** The generated routes are added to the `cli_to_api_router`, which is then included in the main FastAPI application in `src/rb-api/rb/api/main.py`. This makes the plugin's functionality accessible via HTTP requests.

### The `MLService` Helper

To simplify the development of machine learning-based plugins, the project provides a helper class called `MLService` in `src/rb-lib/rb/lib/ml_service.py`. This class offers a structured way to define and manage ML services:

*   **Decorator-Based Approach:** The `add_ml_service` decorator simplifies the creation of `typer` commands and their corresponding API endpoints. It handles the boilerplate code for defining routes, generating task schemas, and managing request/response models.

*   **Metadata and Schema:** The `MLService` class also provides methods for adding metadata to the plugin and defining `TaskSchema` for each ML task. The `TaskSchema` defines the expected inputs and parameters for a given task, which is crucial for validation and for the frontend to dynamically generate user interfaces.

### Input, Output, and Validation

The RescueBox plugin architecture places a strong emphasis on data validation to ensure the stability and reliability of the system. This is achieved through a combination of Pydantic models and custom validation logic:

1.  **Pydantic Models:** The `src/rb-api/rb/api/models.py` file defines a comprehensive set of Pydantic models for API requests and responses. These models define the data structures for inputs, outputs, and task schemas, ensuring that all data exchanged between the frontend, API, and backend plugins is well-structured and validated.

2.  **Type Hint Validation:** The `src/rb-lib/rb/lib/utils.py` module provides functions that enforce consistency between the type hints in a plugin's ML function and the `TaskSchema` defined for that function. The `ensure_ml_func_hinting_and_task_schemas_are_valid` function is particularly important, as it checks that the data types of the function's arguments match the types specified in the schema. This prevents data type mismatches and ensures that the backend functions receive the data in the expected format.

3.  **Exception Handling:** The FastAPI application includes a global exception handler in `src/rb-api/rb/api/main.py` that catches and formats validation errors from the backend plugins. This ensures that the API provides consistent and informative error responses.

### Plugin Invocation

Plugins can be invoked in two ways:

1.  **CLI:** From the command line, plugins are invoked as subcommands of the main `rescuebox` command. For example, a command in the `file-utils` plugin would be invoked as `rescuebox fs <command>`.

2.  **API:** Plugins are invoked via HTTP requests to the dynamically generated API endpoints. The specific endpoint for a given command can be discovered by querying the `/api/routes` endpoint of the plugin.

### Plugin Testing

The `src/rb-lib/rb/lib/common_tests.py` file provides a base class, `RBAppTest`, which simplifies the process of writing tests for plugins. This class includes helper methods for testing the CLI commands, API endpoints, metadata, and task schemas, ensuring that plugins are working correctly and are well-integrated into the RescueBox ecosystem.

## Backend

The backend of the RescueBox project is contained within the `rescuebox` and `src` directories. The `rescuebox` directory contains the core CLI application, while the `src` directory holds all the plugins. The file `c:\work\rel\RescueBox\rescuebox\plugins\__init__.py` is responsible for importing and collecting all the backend plugins from the `src` directory.

## API Backend

The RescueBox project also includes a FastAPI application that exposes the functionality of the plugins through a RESTful API. The main entry point for this application is `c:\work\rel\RescueBox\src\rb-api\rb\api\main.py`. This file is responsible for creating the FastAPI application and including the API routers from `rb.api.routes`.

The file `c:\work\rel\RescueBox\src\rb-api\rb\api\routes\cli.py` is responsible for dynamically generating API routes from the CLI commands defined in the plugins. It inspects the `typer` commands and creates corresponding FastAPI endpoints, effectively exposing the CLI functionality through the API. This includes both static and streaming endpoints, with the `command_callback` function creating the appropriate handler for each command.

Additionally, the file `c:\work\rel\RescueBox\src\rb-api\rb\api\routes\ui.py` provides the backend with a simple web-based user interface for developers. This "dev UI" or "react UI" renders a tree of all available backend commands. The frontend for this interface is a React application located in `c:\work\rel\RescueBox\web\rescuebox-autoui`, which consumes the data from the API and provides an interactive way to execute commands and view their output. The endpoint URLs are constructed in the typer_app_to_tree function, which is responsible for generating the data structure used by the frontend.

The `validation_exception_handler` function in this file is a global exception handler that catches and formats validation errors from any of the backend plugins, ensuring a consistent error response format across the API.

## Frontend

The RescueBox project also includes a desktop application, `RescueBox-Desktop`. This is an Electron application built with the following technologies:

*   **Framework:** React
*   **Language:** TypeScript
*   **Bundler:** Webpack
*   **UI Components:** Radix UI, shadcn/ui
*   **Styling:** Tailwind CSS

This application provides a graphical user interface for interacting with the RescueBox plugins and viewing the results of their analyses.

## Development

The `CONTRIBUTING.md` file contains detailed instructions for developers who wish to contribute to the project. It covers topics such as reporting bugs, suggesting enhancements, and submitting code changes.