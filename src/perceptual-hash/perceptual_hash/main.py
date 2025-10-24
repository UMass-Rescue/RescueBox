"""Main plugin file for Perceptual Hash plugin."""

import json
import logging
import os
from pathlib import Path
from typing import List, TypedDict, Optional
import typer

from rb.lib.ml_service import MLService
from rb.api.models import (
    BatchFileInput,
    BatchFileResponse,
    DirectoryInput,
    EnumParameterDescriptor,
    EnumVal,
    FileInput,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextParameterDescriptor,
    TextResponse,
    TextInput,
    RangedFloatParameterDescriptor,
    FloatRangeDescriptor,
)

from perceptual_hash.database import HashDatabase
from perceptual_hash.hasher import PerceptualHasher

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

APP_NAME = "perceptual-hash"
ml_service = MLService(APP_NAME)

# Load app info
script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")

try:
    with open(info_file_path, "r") as f:
        info = f.read()
except FileNotFoundError:
    info = "Perceptual hashing plugin for detecting duplicate and near-duplicate media."

ml_service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Perceptual Hash",
    author="RescueBox Team",
    version="0.1.0",
    info=info,
)

# Supported algorithms
supported_algorithms = PerceptualHasher.get_supported_algorithms()


def get_available_collections():
    """Get available collections using context manager."""
    try:
        with HashDatabase() as db:
            return db.get_available_collections()
    except Exception as e:
        logger.error(f"Error getting available collections: {e}")
        return []


"""
******************************************************************************************************
Endpoint 1: Create Database (Hash Directory)
******************************************************************************************************
"""


class CreateDatabaseInputs(TypedDict):
    """Inputs for creating a hash database from a directory."""
    media_directory: DirectoryInput


class CreateDatabaseParameters(TypedDict):
    """Parameters for creating a hash database."""
    collection_name: str
    hash_algorithm: str
    recursive: str


def create_database_task_schema() -> TaskSchema:
    """Task schema for creating a hash database."""
    return TaskSchema(
        inputs=[
            InputSchema(
                key="media_directory",
                label="Media Directory",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=TextParameterDescriptor(
                    default="my_collection",
                    placeholder="Enter collection name",
                ),
            ),
            ParameterSchema(
                key="hash_algorithm",
                label="Hash Algorithm",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=algo, label=PerceptualHasher.get_algorithm_info(algo)["name"])
                        for algo in supported_algorithms
                    ],
                    default="phash",
                ),
            ),
            ParameterSchema(
                key="recursive",
                label="Recursive",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key="true", label="Yes"),
                        EnumVal(key="false", label="No"),
                    ],
                    default="true",
                ),
            ),
        ],
    )


def create_database(
    inputs: CreateDatabaseInputs,
    parameters: CreateDatabaseParameters
) -> ResponseBody:
    """
    Create a database of perceptual hashes from a directory of media files.
    
    Args:
        inputs: Directory containing media files
        parameters: Collection name, hash algorithm, and recursive flag
        
    Returns:
        Response with success message and statistics
    """
    try:
        media_directory = inputs["media_directory"].path
        collection_name = parameters["collection_name"]
        hash_algorithm = parameters["hash_algorithm"]
        recursive = parameters["recursive"] == "true"
        
        logger.info(
            f"Creating hash database '{collection_name}' using {hash_algorithm} "
            f"from directory: {media_directory}"
        )
        
        # Initialize hasher
        hasher = PerceptualHasher(hash_algorithm)
        
        # Compute hashes for all files in directory
        hashes = hasher.compute_directory_hashes(
            str(media_directory),
            recursive=recursive
        )
        
        if not hashes:
            return ResponseBody(
                root=TextResponse(
                    value=f"No supported media files found in {media_directory}"
                )
            )
        
        # Use context manager for database operations
        with HashDatabase() as db:
            # Add hashes to database
            db.add_hashes(collection_name, hash_algorithm, hashes)
            
            # Get statistics
            stats = db.get_collection_stats(collection_name, hash_algorithm)
        
        result = TextResponse(
            value=f"Successfully created collection '{collection_name}' with "
                  f"{len(hashes)} hashes using {hash_algorithm} algorithm. "
                  f"Total hashes in collection: {stats['total_hashes']}"
        )
        return ResponseBody(root=result)
        
    except Exception as e:
        logger.error(f"Error creating database: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def create_database_cli_parser(value: str):
    """Parse CLI input for create_database endpoint."""
    try:
        parts = value.split(",")
        media_directory = parts[0].strip()
        return CreateDatabaseInputs(
            media_directory=DirectoryInput(path=media_directory)
        )
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        raise typer.Abort()


def create_database_param_parser(value: str):
    """Parse CLI parameters for create_database endpoint."""
    try:
        parts = value.split(",")
        collection_name = parts[0].strip() if len(parts) > 0 else "my_collection"
        hash_algorithm = parts[1].strip() if len(parts) > 1 else "pdq"
        recursive = parts[2].strip() if len(parts) > 2 else "true"
        return CreateDatabaseParameters(
            collection_name=collection_name,
            hash_algorithm=hash_algorithm,
            recursive=recursive,
        )
    except Exception as e:
        logger.error(f"Error parsing CLI parameters: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/create_database",
    ml_function=create_database,
    inputs_cli_parser=typer.Argument(
        parser=create_database_cli_parser,
        help="Media directory path",
    ),
    parameters_cli_parser=typer.Option(
        None,
        "--params",
        parser=create_database_param_parser,
        help="collection_name,hash_algorithm,recursive",
    ),
    task_schema_func=create_database_task_schema,
    short_title="Create Hash Database",
    order=0,
)


"""
******************************************************************************************************
Endpoint 2: Find Matches (Query Database)
******************************************************************************************************
"""


class FindMatchesInputs(TypedDict):
    """Inputs for finding matches."""
    query_directory: DirectoryInput
    output_file: FileInput


class FindMatchesParameters(TypedDict):
    """Parameters for finding matches."""
    collection_name: str
    hash_algorithm: str
    max_distance: float
    max_results: float


def find_matches_task_schema() -> TaskSchema:
    """Task schema for finding matches."""
    # Get available collections
    available_collections = ["Select a collection"] + get_available_collections()
    
    return TaskSchema(
        inputs=[
            InputSchema(
                key="query_directory",
                label="Query Directory",
                input_type=InputType.DIRECTORY,
            ),
            InputSchema(
                key="output_file",
                label="Output JSON File",
                input_type=InputType.FILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=name, label=name)
                        for name in available_collections[1:]
                    ],
                    message_when_empty="No collections found. Create one first.",
                    default=available_collections[0],
                ),
            ),
            ParameterSchema(
                key="hash_algorithm",
                label="Hash Algorithm",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=algo, label=PerceptualHasher.get_algorithm_info(algo)["name"])
                        for algo in supported_algorithms
                    ],
                    default="phash",
                ),
            ),
            ParameterSchema(
                key="max_distance",
                label="Maximum Distance Threshold (Hamming)",
                value=RangedFloatParameterDescriptor(
                    range=FloatRangeDescriptor(min=0.0, max=100.0),
                    default=10.0,
                ),
            ),
            ParameterSchema(
                key="max_results",
                label="Maximum Results per Query",
                value=RangedFloatParameterDescriptor(
                    range=FloatRangeDescriptor(min=1.0, max=100.0),
                    default=10.0,
                ),
            ),
        ],
    )


def find_matches(
    inputs: FindMatchesInputs,
    parameters: FindMatchesParameters
) -> ResponseBody:
    """
    Find matching media files in the database.
    
    Args:
        inputs: Query directory containing files to search for
        parameters: Collection name, hash algorithm, and search parameters
        
    Returns:
        Response with success message and output file path
    """
    try:
        query_directory = inputs["query_directory"].path
        output_file = inputs["output_file"].path
        collection_name = parameters["collection_name"]
        hash_algorithm = parameters["hash_algorithm"]
        max_distance = float(parameters["max_distance"])
        max_results = int(float(parameters["max_results"]))
        
        logger.info(
            f"Finding matches for files in {query_directory} in collection "
            f"'{collection_name}' using {hash_algorithm}"
        )
        
        # Initialize hasher
        hasher = PerceptualHasher(hash_algorithm)
        
        # Compute hashes for all files in query directory
        query_hashes = hasher.compute_directory_hashes(
            str(query_directory),
            recursive=False  # Only search immediate directory
        )
        
        if not query_hashes:
            return ResponseBody(
                root=TextResponse(value=f"No supported media files found in {query_directory}")
            )
        
        # Query database using context manager
        with HashDatabase() as db:
            results = db.query_hashes(
                collection_name,
                hash_algorithm,
                query_hashes,
                n_results=max_results,
                threshold=max_distance,
            )
        
        # Build JSON output structure
        json_output = {
            "metadata": {
                "collection_name": collection_name,
                "hash_algorithm": hash_algorithm,
                "max_distance": max_distance,
                "max_results_per_query": max_results,
                "total_query_files": len(query_hashes),
                "total_matches_found": 0
            },
            "results": {}
        }
        
        total_matches = 0
        for query_hash, matches in zip(query_hashes, results):
            query_path = query_hash["file_path"]
            
            # Build matches list for this query
            match_list = []
            for match in matches:
                hamming_distance = match.get("hamming_distance", match["distance"])
                similarity = match["similarity"]
                
                # Determine match quality based on Hamming distance
                if hamming_distance < 5:
                    quality = "exact"
                elif hamming_distance < 10:
                    quality = "very_similar"
                elif hamming_distance < 20:
                    quality = "similar"
                else:
                    quality = "somewhat_similar"
                
                match_list.append({
                    "file_path": match["file_path"],
                    "hamming_distance": int(hamming_distance),
                    "similarity": similarity,
                    "quality": quality
                })
                total_matches += 1
            
            json_output["results"][query_path] = {
                "matches": match_list,
                "total_matches": len(match_list)
            }
        
        json_output["metadata"]["total_matches_found"] = total_matches
        
        # Write output to file
        with open(output_file, 'w') as f:
            json.dump(json_output, f, indent=2)
        
        result = TextResponse(
            value=f"Successfully found {total_matches} matches for {len(query_hashes)} query files. "
                  f"Results saved to {output_file}"
        )
        return ResponseBody(root=result)
        
    except Exception as e:
        logger.error(f"Error finding matches: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def find_matches_cli_parser(value: str):
    """Parse CLI input for find_matches endpoint."""
    try:
        parts = value.split(",")
        query_directory = parts[0].strip()
        output_file = parts[1].strip() if len(parts) > 1 else "matches.json"
        return FindMatchesInputs(
            query_directory=DirectoryInput(path=query_directory),
            output_file=FileInput(path=output_file)
        )
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        raise typer.Abort()


def find_matches_param_parser(value: str):
    """Parse CLI parameters for find_matches endpoint."""
    try:
        parts = value.split(",")
        collection_name = parts[0].strip() if len(parts) > 0 else "my_collection"
        hash_algorithm = parts[1].strip() if len(parts) > 1 else "phash"
        max_distance = float(parts[2].strip()) if len(parts) > 2 else 10.0
        max_results = float(parts[3].strip()) if len(parts) > 3 else 10.0
        return FindMatchesParameters(
            collection_name=collection_name,
            hash_algorithm=hash_algorithm,
            max_distance=max_distance,
            max_results=max_results,
        )
    except Exception as e:
        logger.error(f"Error parsing CLI parameters: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/find_matches",
    ml_function=find_matches,
    inputs_cli_parser=typer.Argument(
        parser=find_matches_cli_parser,
        help="query_directory,output_file",
    ),
    parameters_cli_parser=typer.Option(
        None,
        "--params",
        parser=find_matches_param_parser,
        help="collection_name,hash_algorithm,max_distance,max_results",
    ),
    task_schema_func=find_matches_task_schema,
    short_title="Find Matches",
    order=1,
)


"""
******************************************************************************************************
Endpoint 3: Export Database
******************************************************************************************************
"""


class ExportDatabaseInputs(TypedDict):
    """Inputs for exporting a database."""
    output_file: FileInput


class ExportDatabaseParameters(TypedDict):
    """Parameters for exporting a database."""
    collection_name: str
    hash_algorithm: str


def export_database_task_schema() -> TaskSchema:
    """Task schema for exporting a database."""
    available_collections = ["Select a collection"] + get_available_collections()
    
    return TaskSchema(
        inputs=[
            InputSchema(
                key="output_file",
                label="Output JSON File",
                input_type=InputType.FILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=name, label=name)
                        for name in available_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=available_collections[0],
                ),
            ),
            ParameterSchema(
                key="hash_algorithm",
                label="Hash Algorithm",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=algo, label=PerceptualHasher.get_algorithm_info(algo)["name"])
                        for algo in supported_algorithms
                    ],
                    default="phash",
                ),
            ),
        ],
    )


def export_database(
    inputs: ExportDatabaseInputs,
    parameters: ExportDatabaseParameters
) -> ResponseBody:
    """
    Export a hash collection to a JSON file.
    
    Args:
        inputs: Output file path
        parameters: Collection name and hash algorithm
        
    Returns:
        Response with success message
    """
    try:
        output_file = inputs["output_file"].path
        collection_name = parameters["collection_name"]
        hash_algorithm = parameters["hash_algorithm"]
        
        logger.info(f"Exporting collection '{collection_name}' ({hash_algorithm}) to {output_file}")
        
        # Export using context manager
        with HashDatabase() as db:
            db.export_collection(collection_name, hash_algorithm, str(output_file))
            stats = db.get_collection_stats(collection_name, hash_algorithm)
        
        result = TextResponse(
            value=f"Successfully exported collection '{collection_name}' ({hash_algorithm}) "
                  f"with {stats['total_hashes']} hashes to {output_file}"
        )
        return ResponseBody(root=result)
        
    except Exception as e:
        logger.error(f"Error exporting database: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def export_database_cli_parser(value: str):
    """Parse CLI input for export_database endpoint."""
    try:
        return ExportDatabaseInputs(
            output_file=FileInput(path=value.strip())
        )
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        raise typer.Abort()


def export_database_param_parser(value: str):
    """Parse CLI parameters for export_database endpoint."""
    try:
        parts = value.split(",")
        collection_name = parts[0].strip() if len(parts) > 0 else "my_collection"
        hash_algorithm = parts[1].strip() if len(parts) > 1 else "phash"
        return ExportDatabaseParameters(
            collection_name=collection_name,
            hash_algorithm=hash_algorithm,
        )
    except Exception as e:
        logger.error(f"Error parsing CLI parameters: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/export_database",
    ml_function=export_database,
    inputs_cli_parser=typer.Argument(
        parser=export_database_cli_parser,
        help="Output JSON file path",
    ),
    parameters_cli_parser=typer.Option(
        None,
        "--params",
        parser=export_database_param_parser,
        help="collection_name,hash_algorithm",
    ),
    task_schema_func=export_database_task_schema,
    short_title="Export Hash Database",
    order=2,
)


"""
******************************************************************************************************
Endpoint 4: Import Database
******************************************************************************************************
"""


class ImportDatabaseInputs(TypedDict):
    """Inputs for importing a database."""
    input_file: FileInput


class ImportDatabaseParameters(TypedDict):
    """Parameters for importing a database."""
    new_collection_name: str


def import_database_task_schema() -> TaskSchema:
    """Task schema for importing a database."""
    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_file",
                label="Input JSON File",
                input_type=InputType.FILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="new_collection_name",
                label="New Collection Name (optional)",
                value=TextParameterDescriptor(
                    default="",
                    placeholder="Leave empty to use original name",
                ),
            ),
        ],
    )


def import_database(
    inputs: ImportDatabaseInputs,
    parameters: ImportDatabaseParameters
) -> ResponseBody:
    """
    Import a hash collection from a JSON file.
    
    Args:
        inputs: Input file path
        parameters: Optional new collection name
        
    Returns:
        Response with success message
    """
    try:
        input_file = inputs["input_file"].path
        new_collection_name = parameters["new_collection_name"] if parameters["new_collection_name"] else None
        
        logger.info(f"Importing collection from {input_file}")
        
        # Import using context manager
        with HashDatabase() as db:
            db.import_collection(str(input_file), new_collection_name)
        
        collection_name = new_collection_name if new_collection_name else "original"
        result = TextResponse(
            value=f"Successfully imported collection '{collection_name}' from {input_file}"
        )
        return ResponseBody(root=result)
        
    except Exception as e:
        logger.error(f"Error importing database: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def import_database_cli_parser(value: str):
    """Parse CLI input for import_database endpoint."""
    try:
        return ImportDatabaseInputs(
            input_file=FileInput(path=value.strip())
        )
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        raise typer.Abort()


def import_database_param_parser(value: str):
    """Parse CLI parameters for import_database endpoint."""
    try:
        new_collection_name = value.strip() if value else ""
        return ImportDatabaseParameters(
            new_collection_name=new_collection_name,
        )
    except Exception as e:
        logger.error(f"Error parsing CLI parameters: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/import_database",
    ml_function=import_database,
    inputs_cli_parser=typer.Argument(
        parser=import_database_cli_parser,
        help="Input JSON file path",
    ),
    parameters_cli_parser=typer.Option(
        None,
        "--params",
        parser=import_database_param_parser,
        help="new_collection_name (optional)",
    ),
    task_schema_func=import_database_task_schema,
    short_title="Import Hash Database",
    order=3,
)


"""
******************************************************************************************************
Endpoint 5: List Collections
******************************************************************************************************
"""


class ListCollectionsInputs(TypedDict):
    """Inputs for listing collections."""
    dummy: TextInput  # Workaround for AutoUI - required to send request body


def list_collections_task_schema() -> TaskSchema:
    """Task schema for listing collections."""
    return TaskSchema(
        inputs=[
            InputSchema(
                key="dummy",
                label="List Collections",
                input_type=InputType.TEXT,
            )
        ],
        parameters=[],
    )


def list_collections(
    inputs: ListCollectionsInputs
) -> ResponseBody:
    """
    List all available hash collections.

    Args:
        inputs: No inputs required
        parameters: No parameters required

    Returns:
        Response with list of collections and their statistics
    """
    try:
        logger.info("Listing all collections")

        with HashDatabase() as db:
            available_collections = db.get_available_collections()

            if not available_collections:
                return ResponseBody(root=TextResponse(value="No collections found."))

            output_lines = ["Available Collections:"]

            for collection_name in available_collections:
                output_lines.append(f"\n{collection_name}:")
                for algo in supported_algorithms:
                    try:
                        stats = db.get_collection_stats(collection_name, algo)
                        if stats["total_hashes"] > 0:
                            vector_dim = stats.get("vector_dimension", "unknown")
                            output_lines.append(
                                f"  - {algo}: {stats['total_hashes']} hashes (dimension: {vector_dim})"
                            )
                    except Exception:
                        # Collection doesn't exist for this algorithm
                        pass

        result_text = "\n".join(output_lines)
        return ResponseBody(root=TextResponse(value=result_text))

    except Exception as e:
        logger.error(f"Error listing collections: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def list_collections_cli_parser(value: str):
    """Parse CLI input for list_collections endpoint."""
    return ListCollectionsInputs(dummy=TextInput(text=""))


ml_service.add_ml_service(
    rule="/list_collections",
    ml_function=list_collections,
    inputs_cli_parser=typer.Argument(
        default="",
        parser=list_collections_cli_parser,
        help="(no inputs required)",
    ),
    task_schema_func=list_collections_task_schema,
    short_title="List Collections",
    order=4,
)


"""
******************************************************************************************************
Endpoint 6: Delete Collection
******************************************************************************************************
"""


class DeleteCollectionInputs(TypedDict):
    """Inputs for deleting a collection."""
    dummy: TextInput  # Workaround for AutoUI - required to send request body


class DeleteCollectionParameters(TypedDict):
    """Parameters for deleting a collection."""
    collection_name: str
    hash_algorithm: str


def delete_collection_task_schema() -> TaskSchema:
    """Task schema for deleting a collection."""
    available_collections = ["Select a collection"] + get_available_collections()

    return TaskSchema(
        inputs=[
            InputSchema(
                key="dummy",
                label="Delete Collection",
                input_type=InputType.TEXT,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=name, label=name)
                        for name in available_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=available_collections[0],
                ),
            ),
            ParameterSchema(
                key="hash_algorithm",
                label="Hash Algorithm",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=algo, label=PerceptualHasher.get_algorithm_info(algo)["name"])
                        for algo in supported_algorithms
                    ],
                    default="phash",
                ),
            ),
        ],
    )


def delete_collection(
    inputs: DeleteCollectionInputs,
    parameters: DeleteCollectionParameters
) -> ResponseBody:
    """
    Delete a hash collection.

    Args:
        inputs: No inputs required
        parameters: Collection name and hash algorithm

    Returns:
        Response with success message
    """
    try:
        collection_name = parameters["collection_name"]
        hash_algorithm = parameters["hash_algorithm"]

        logger.info(f"Deleting collection '{collection_name}' ({hash_algorithm})")

        # Delete using context manager
        with HashDatabase() as db:
            db.delete_collection(collection_name, hash_algorithm)

        result = TextResponse(
            value=f"Successfully deleted collection '{collection_name}' ({hash_algorithm})"
        )
        return ResponseBody(root=result)

    except Exception as e:
        logger.error(f"Error deleting collection: {e}", exc_info=True)
        return ResponseBody(root=TextResponse(value=f"Error: {str(e)}"))


def delete_collection_cli_parser(value: str):
    """Parse CLI input for delete_collection endpoint."""
    return DeleteCollectionInputs(dummy=TextInput(text=""))


def delete_collection_param_parser(value: str):
    """Parse CLI parameters for delete_collection endpoint."""
    try:
        parts = value.split(",")
        collection_name = parts[0].strip() if len(parts) > 0 else "my_collection"
        hash_algorithm = parts[1].strip() if len(parts) > 1 else "phash"
        return DeleteCollectionParameters(
            collection_name=collection_name,
            hash_algorithm=hash_algorithm,
        )
    except Exception as e:
        logger.error(f"Error parsing CLI parameters: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/delete_collection",
    ml_function=delete_collection,
    inputs_cli_parser=typer.Argument(
        default="",
        parser=delete_collection_cli_parser,
        help="(no inputs required)",
    ),
    parameters_cli_parser=typer.Option(
        None,
        "--params",
        parser=delete_collection_param_parser,
        help="collection_name,hash_algorithm",
    ),
    task_schema_func=delete_collection_task_schema,
    short_title="Delete Hash Collection",
    order=5,
)


# Export the app
app = ml_service.app

if __name__ == "__main__":
    app()