import inspect
import typing

from rb.api.models import InputType
import typer
from anytree import Node


def get_inputs_from_signature(
    signature: inspect.Signature,
    command: typing.Optional[typer.models.CommandInfo] = None,
    schema_commands: dict = None,
) -> list[dict]:
    result = []

    # --- New MLService-specific logic ---
    # get the schema from the 'endpoint' object in the command's closure.
    task_schema = None
    if command and schema_commands:
        command_name = getattr(command, "name", None) or command.callback.__name__
        schema_command_name = f"{command_name}/task_schema"
        if not command_name.endswith("/task_schema"):
            schema_command = schema_commands.get(schema_command_name)
            if schema_command:
                try:
                    # The 'endpoint' variable is captured by the 'run' function's closure inside MLService.
                    endpoint_idx = schema_command.callback.__code__.co_freevars.index(
                        "endpoint"
                    )
                    endpoint = schema_command.callback.__closure__[
                        endpoint_idx
                    ].cell_contents

                    if endpoint and hasattr(endpoint, "task_schema_func"):
                        task_schema = endpoint.task_schema_func()
                        if task_schema.inputs:
                            for an_input in task_schema.inputs:
                                result.append(
                                    {
                                        "name": an_input.key,
                                        "type": an_input.input_type.value,
                                        "help": an_input.label,
                                        "is_parameter": False,
                                        "is_file_path": an_input.input_type
                                        == InputType.FILE,
                                        "is_dir_path": an_input.input_type
                                        == InputType.DIRECTORY,
                                        "is_text": an_input.input_type
                                        == InputType.TEXT,
                                    }
                                )
                        if task_schema.parameters:
                            for a_param in task_schema.parameters:
                                result.append(
                                    {
                                        "name": a_param.key,
                                        "type": a_param.value.parameter_type.value,
                                        "help": a_param.label,
                                        "default": a_param.value.default,
                                        "is_parameter": True,
                                        "is_file_path": False,
                                    }
                                )
                        return result
                except (ValueError, IndexError, AttributeError):
                    pass

    for param in signature.parameters.values():

        data = {
            "name": param.name,
        }

        if typing.get_origin(param.annotation) == typing.Annotated:
            data["type"] = typing.get_args(param.annotation)[0].__name__
            data["help"] = typing.get_args(param.annotation)[1].help
        else:
            data["type"] = param.annotation.__name__

        if isinstance(param.default, typer.models.OptionInfo):
            data["default"] = param.default.default
            data["help"] = param.default.help
        elif isinstance(param.default, typer.models.ArgumentInfo):
            data["help"] = param.default.help
        elif param.default is not inspect.Parameter.empty:
            data["default"] = param.default
        else:
            data["default"] = None
        result.append(data)
    return result

def typer_app_to_tree(app: typer.Typer) -> dict:
    # Create root node
    root = Node("rescuebox", command=None, is_group=True)
    schema_commands = {}

    def add_commands_to_node(typer_app: typer.Typer, parent_node: Node):
        
        for group in getattr(typer_app, "registered_groups", []):
            group_node = Node(
                group.name,
                parent=parent_node,
                command=None,
                is_group=True,
            )
            # Recursively add any nested groups/commands
            add_commands_to_node(group.typer_instance, group_node)

        # Add commands at this level, building a map of schema commands first.
        for command in getattr(typer_app, "registered_commands", []):
            command_name = getattr(command, "name", None) or command.callback.__name__
            if command_name.endswith("/task_schema"):
                schema_commands[command_name] = command

            Node(
                command_name,
                parent=parent_node,
                command=command,
                is_group=False,
                signature=inspect.signature(command.callback),
            )

    # Build the full tree structure
    add_commands_to_node(app, root)

    def get_endpoint_from_schema(command: typer.models.CommandInfo):
        if not command or not schema_commands:
            return None
        command_name = getattr(command, "name", None) or command.callback.__name__
        schema_command = schema_commands.get(f"{command_name}/task_schema")
        if not schema_command:
            return None
        try:
            endpoint_idx = schema_command.callback.__code__.co_freevars.index(
                "endpoint"
            )
            return schema_command.callback.__closure__[endpoint_idx].cell_contents
        except (ValueError, IndexError, AttributeError):
            return None

    def node_to_dict(node: Node) -> dict:
        result = {
            "name": node.name,
            "is_group": node.is_group,
            "help": None,
            "order": 0,
        }
        endpoint = get_endpoint_from_schema(node.command)

        if endpoint:
            result["order"] = endpoint.order

        if not node.is_group:
            result["endpoint"] = "/" + "/".join([_.name for _ in node.path][1:])

            result["inputs"] = get_inputs_from_signature(
                node.signature, node.command, schema_commands
            )
            if (
                endpoint
                or node.name.endswith("/task_schema")
                or node.name.endswith("/routes")
                or node.name.endswith("/app_metadata")
            ):
                result["endpoint"] = node.name
            result["help"] = node.command.callback.__doc__
            if result["help"] is None:
                result["help"] = node.command.help

        if node.children:
            children_as_dicts = [node_to_dict(child) for child in node.children]
            result["children"] = children_as_dicts
            if endpoint:
                sorted_children = sorted(
                    children_as_dicts, key=lambda x: x.get("order", 0)
                )
                result["children"] = sorted_children
        return result

    # Convert the entire tree to dictionary format
    tree_dict = node_to_dict(root)
    return tree_dict
