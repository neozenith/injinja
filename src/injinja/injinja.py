# ruff: noqa: E501
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "jinja2",
#   "PyYAML",
#   "deepmerge",
#   "types-PyYAML",
#   "types-jinja2",
#   "jsonschema",
#   "pydantic"
# ]
# ///
# https://docs.astral.sh/uv/guides/scripts/#creating-a-python-script
# https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata


# Standard Library
import argparse
import difflib
import functools
import importlib.util
import itertools
import json
import logging
import os
import pathlib
import shlex
import sys
import textwrap
import tomllib
from typing import Any, cast

# Third Party
import jinja2
import jsonschema
import yaml
from deepmerge import always_merger
from jinja2.filters import FILTERS
from jinja2.tests import TESTS
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass

DEBUG_MODE = False
TRACEBACK_SUPPRESSIONS = [jinja2]
if "--debug" in sys.argv:  # Finished with debug flag so it is safe to remove at this point.
    DEBUG_MODE = True
    sys.argv.remove("--debug")

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
log_format = (
    "%(asctime)s::%(name)s::%(levelname)s::%(module)s:%(funcName)s:%(lineno)d| %(message)s"
    if DEBUG_MODE
    else "%(message)s"
)
log_date_format = "%Y-%m-%d %H:%M:%S"

CLI_CONFIG: dict[str, Any] = {
    "debug": True,
    # Gathering Environment variables for dynamic configuration
    "env": {
        "action": "append",
        "default": [],
        "help": "Environment variables to pass to the template. Can be KEY=VALUE or path to an .env file.",
    },
    "prefix": {
        "default": [],
        "action": "append",
        "help": "Import all environment variables with given prefix. eg 'MYAPP_' could find MYAPP_NAME and will import as `myapp.name`. This argument can be repeated.",
    },
    # Gather static configuration files
    "config": {
        "required": False,
        "default": [],
        "action": "append",
        "help": """
               The configuration file(s) to use. 
               Either specify a single file, repeated config flags for multiple files or a glob pattern.
        """,
    },
    # Target Jinja template file
    "template": {"required": False, "help": "The Jinja2 template file to use."},
    "functions": {
        "required": False,
        "default": [],
        "action": "append",
        "help": "Path or glob pattern to a python file containing custom functions to use in the template.",
    },
    # Output file / stdout
    "output": "stdout",
    "validate": {"help": "Filename of an outputfile to validate the output against."},
    "stdin-format": {  # New argument for stdin format
        "required": False,
        "default": None,
        "choices": ["json", "yml", "yaml", "toml"],
        "help": "Format of the configuration data piped via stdin (json, yaml, toml). If set, injinja will attempt to read from stdin. eg cat config.json | python3 injinja.py --stdin-format json",
    },
    "schema": {  # Schema validation file
        "required": False,
        "default": None,
        "help": "Schema file to validate the final merged configuration. JSON Schema files (.json) or Pydantic models (schema_models.py::MyModel).",
    },
}


########################################################################################
# CLI
########################################################################################


def __argparse_factory(config: dict[str, Any]) -> argparse.ArgumentParser:
    """Opinionated Argument Parser Factory."""
    parser = argparse.ArgumentParser(
        prog="Injinja",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""Injinja: Injectable Jinja Configuration tool. Insanely configurable... config system.

        - Collate DYNAMIC configuration from environment variables using --env, --prefix flags
        - Collate the STATIC configuration (files) using the --config flags.
        - DYNAMIC config templates the STATIC config.
        - The _Templated STATIC Config_ is then applied to your target Jinja2 template file using the --template flag.
        - The output is then rendered to either stdout or a target file.

        OPTIONALLY:
        - Can take custom Jinja2 Functions to inject into the Jinja2 Templating Engine Environment
        - Can take a validation file to assist with checking expected templated output against a known file.
        """),
    )

    # Take a dictionary of configuration. The key is the flag name, the value is a dictionary of kwargs.
    for flag, flag_kwargs in config.items():
        # Automatically handle long and short case for flags
        lowered_flag = flag.lower()
        short_flag = f"-{lowered_flag[0]}"
        long_flag = f"--{lowered_flag}"

        # If the value of the config dict is a dictionary then unpack it like standard kwargs for add_argument
        # Otherwise assume the value is a simple default value like a string.
        if isinstance(flag_kwargs, dict):
            parser.add_argument(short_flag, long_flag, **flag_kwargs)
        elif isinstance(flag_kwargs, bool):
            store_type = "store_true" if flag_kwargs else "store_false"
            parser.add_argument(short_flag, long_flag, action=store_type)
        else:
            parser.add_argument(short_flag, long_flag, default=flag_kwargs)
    return parser


def __handle_args(parser: argparse.ArgumentParser, args: list[str] | None) -> dict[str, Any]:
    """Handle CLI arguments into structured dictionary output."""
    script_filename = pathlib.Path(__file__).name
    # log.info(script_filename)
    if args is not None and script_filename in args:
        args.remove(script_filename)
    return vars(parser.parse_args(args))


########################################################################################
# Environment Variables Helpers
########################################################################################


def __expand_files_or_globs_list(files_or_globs: list[str]) -> list[str]:
    """Given a list of files or glob patterns, expand them all and return a list of files."""
    return list(itertools.chain.from_iterable([expand_files_list(x) for x in files_or_globs]))


def expand_files_list(file_or_glob: str) -> list[str]:
    """Automatically determine if a string is a file already or a glob pattern and expand it.
    Always return the resolved list of files."""
    if pathlib.Path(file_or_glob).is_file():
        return [file_or_glob]
    return [str(p) for p in pathlib.Path().glob(file_or_glob)]


def dict_from_keyvalue_list(args: list[str] | None = None) -> dict[str, str] | None:
    """Convert a list of 'key=value' strings into a dictionary."""
    return {k: v for k, v in [x.split("=") for x in args]} if args else None


########################################################################################
# .env Files - Standalone Parser
########################################################################################


def __parse_env_line(line: str) -> tuple[str | None, str | None]:
    """Parses a single line into a key-value pair. Handles quoted values and inline comments.

    Returns (None, None) for invalid lines.
    """
    # Guard checks for empty lines or lines without '='
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None, None

    # Split the line into key and value at the first '='
    key, value = line.split("=", 1)
    key = key.strip()

    # Use shlex to process the value (handles quotes and comments)
    lexer = shlex.shlex(value, posix=True)
    lexer.whitespace_split = True  # Tokenize by whitespace
    value = "".join(lexer)  # Preserve the full quoted/cleaned value

    return key, value


def read_env_file(file_path: str) -> dict[str, str] | None:
    """Reads a .env file and returns a dictionary of key-value pairs.
    If the file does not exist or is not a regular file, returns None.
    """
    file = pathlib.Path(file_path)
    return (
        {
            key: value
            for key, value in map(__parse_env_line, file.read_text().splitlines())
            if key is not None and value is not None
        }
        if file.is_file()
        else None
    )


########################################################################################
# Environment Variables from os.environ by PREFIX_
########################################################################################


def dict_from_prefixes(prefixes: list[str] | None = None) -> dict[str, str] | None:
    """Convert environment variables with a given prefix into a dictionary."""
    if not prefixes:
        return None

    env = os.environ
    return {k.upper(): v for k, v in env.items() for prefix in prefixes if k.lower().startswith(prefix.lower())}


########################################################################################
# Environment Variables - Top Level Handler
########################################################################################


def get_environment_variables(env_flags: list[str], prefixes_list: list[str]) -> dict[str, str]:
    """Get environment variables from all sources and merge them."""

    # Any --env flags that are files are read as .env files
    env_files = [e for e in env_flags if pathlib.Path(e).is_file()]
    # The rest are interpretted as KEY=VALUE pairs
    env_key_values = [e for e in env_flags if e not in env_files]

    env = dict_from_keyvalue_list(env_key_values)
    env_from_files = list(filter(None, [read_env_file(e) for e in env_files]))
    env_from_prefixes = dict_from_prefixes(prefixes_list)

    # Precedence has to be evaluated in this order
    # 1. Environment variables from file(s)
    # 2. Environment variables from prefixes
    # 3. Environment variables from CLI flags
    envs_by_precedence = [*env_from_files, env_from_prefixes, env]

    # Merge environment variables from all sources
    return functools.reduce(always_merger.merge, filter(None, envs_by_precedence), {})


########################################################################################
# Custom Jinja2 Function Loading
########################################################################################


def get_functions(functions: list[str]) -> dict[str, Any]:
    """Load custom functions from python files."""
    all_functions = __expand_files_or_globs_list(functions)

    functions_dict: dict[str, Any] = {"tests": {}, "filters": {}}
    for f in all_functions:
        spec = importlib.util.spec_from_file_location("custom_functions", f)
        log.debug(f"# {spec=}")
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            log.debug(f"# {module=}")
            spec.loader.exec_module(module)
            functions_dict["tests"].update(
                {
                    k.removeprefix("test_"): v
                    for k, v in module.__dict__.items()
                    if callable(v) and k.startswith("test_")
                }
            )
            functions_dict["filters"].update(
                {
                    k.removeprefix("filter_"): v
                    for k, v in module.__dict__.items()
                    if callable(v) and k.startswith("filter_")
                }
            )
    return functions_dict


########################################################################################
# Configuration files and Jinja Templating
########################################################################################


def load_config(filename: str, environment_variables: dict[str, str] | None = None) -> Any:
    """Detect if file is JSON, YAML or TOML and return parsed datastructure.

    When environment_variables is provided, then the file is first treated as a Jinja2 template.
    """
    # Step 1 & 2: Get raw template string and merge config (as necessary), returning as string
    content = merge_template(filename, environment_variables)

    # Step 3: Parse populated string into a data structure.
    if filename.lower().endswith("json"):
        return json.loads(content)
    elif any([filename.lower().endswith(ext) for ext in ["yml", "yaml"]]):
        return yaml.safe_load(content)
    elif filename.lower().endswith("toml"):
        return tomllib.loads(content)

    raise ValueError(f"File type of {filename} not supported.")  # pragma: no cover


def parse_stdin_content(content: str, format_type: str) -> Any:
    """Helper function to parse stdin content based on format."""
    if format_type == "json":
        return json.loads(content)
    elif format_type in ("yaml", "yml"):
        return yaml.safe_load(content)
    elif format_type == "toml":
        return tomllib.loads(content)
    # This case should ideally be caught by argparse choices, but as a fallback:
    raise ValueError(f"Unsupported stdin format: {format_type}")


def merge_template(template_filename: str, config: dict[str, Any] | None) -> str:
    """Load a Jinja2 template from file and merge configuration."""
    # Step 1: get raw content as a string
    raw_content = pathlib.Path(template_filename).read_text()

    # Step 2: Treat raw_content as a Jinja2 template if providing configuration
    if config:
        # NOTE: Providing jinja 2.11.x compatable version to better cross operate
        # with dbt-databricks v1.2.2 and down stream dbt-spark and dbt-core
        try:
            if int(jinja2.__version__[0]) >= 3:  # type: ignore
                content = jinja2.Template(raw_content, undefined=jinja2.StrictUndefined).render(**config)
            else:
                content = jinja2.Template(raw_content).render(**config)
        except jinja2.exceptions.UndefinedError as e:
            log.error(f"{template_filename} UndefinedError: {e}")
            raise

    else:
        content = raw_content

    return content


def map_env_to_confs(config_files_or_globs: list[str], env: dict[str, Any]) -> list[dict[str, Any]]:
    """Load and merge configuration files based on CLI arguments and environment variables.

    The accumulated and merged 'environment variables' is then MAPPED to every config file.
    Eg every config file is treated as a Jinja2 Template and the 'config' of those template IS the environment variables.

    We wind up with a list of configuration dictionaries, each one maps to a single original config file.
    So each STATIC config is populated in isolation with the DYNAMIC config (environment variables).

    The final deepmerged config occurs in reduce_confs.
    """
    log.debug(f"# config sources: {config_files_or_globs=}")
    all_conf_files = __expand_files_or_globs_list(config_files_or_globs)
    log.debug(f"# all_conf_files: {all_conf_files=}")
    confs = [load_config(conf, env) for conf in all_conf_files]
    return confs


def reduce_confs(confs: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce a list of configuration dictionaries into a single dictionary.

    This is the magic!

    The order of your config files is important in how they layer over the top of each other for merging and overrides.
    """
    return functools.reduce(always_merger.merge, confs, {})


########################################################################################
# Schema Validation
########################################################################################


def _load_pydantic_model(schema_spec: str) -> type[BaseModel]:
    """Load a Pydantic model from a module specification.
    
    Args:
        schema_spec: Pydantic model specification in format "module.py::ModelClass"
        
    Returns:
        The Pydantic model class
        
    Raises:
        ConfigValidationError: If the model cannot be loaded
    """
    # Parse the module and class specification
    if "::" not in schema_spec:
        error_msg = f"Pydantic validation failed: Invalid format '{schema_spec}'. Expected format: 'module.py::ModelClass'"
        log.error(error_msg)
        raise ConfigValidationError(error_msg)
        
    module_path, class_name = schema_spec.split("::", 1)
    module_file = pathlib.Path(module_path)
    
    if not module_file.exists():
        error_msg = f"Pydantic validation failed: Module file '{module_path}' not found."
        log.error(error_msg)
        raise ConfigValidationError(error_msg)
        
    # Import the module dynamically
    try:
        spec = importlib.util.spec_from_file_location("schema_module", module_file)
        if spec is None or spec.loader is None:
            error_msg = f"Pydantic validation failed: Could not load module '{module_path}'"
            log.error(error_msg)
            raise ConfigValidationError(error_msg)
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        error_msg = f"Pydantic validation failed: Error loading module '{module_path}': {e}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e
        
    # Get the model class
    if not hasattr(module, class_name):
        available_classes = [name for name in dir(module) if not name.startswith('_') and isinstance(getattr(module, name), type)]
        error_msg = f"Pydantic validation failed: Class '{class_name}' not found in '{module_path}'. Available classes: {', '.join(available_classes)}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg)
        
    model_class = getattr(module, class_name)
    
    # Verify it's a Pydantic model
    if not (isinstance(model_class, type) and issubclass(model_class, BaseModel)):
        error_msg = f"Pydantic validation failed: '{class_name}' is not a Pydantic BaseModel"
        log.error(error_msg)
        raise ConfigValidationError(error_msg)
        
    return model_class


def validate_config_with_pydantic(config: dict[str, Any], schema_spec: str) -> None:
    """Validate the final merged configuration against a Pydantic model.
    
    Args:
        config: The final merged configuration dictionary
        schema_spec: Pydantic model specification in format "module.py::ModelClass"
        
    Raises:
        ConfigValidationError: If validation fails with detailed error message
    """
    try:
        model_class = _load_pydantic_model(schema_spec)
        
        # Validate the configuration
        model_class.model_validate(config)
        print(f"✅ Configuration successfully validated against Pydantic model '{schema_spec}'")
        
    except ValidationError as e:
        error_details = ["Pydantic validation failed:"]
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"]) if error["loc"] else "root"
            error_details.append(f"  Error at path: {location}")
            error_details.append(f"  Message: {error['msg']}")
            if "input" in error:
                error_details.append(f"  Input value: {error['input']}")
        error_details.append(f"  Model: {schema_spec}")
        error_msg = "\n".join(error_details)
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e
    except ConfigValidationError:
        # Re-raise ConfigValidationError as-is
        raise
    except Exception as e:
        error_msg = f"Pydantic validation failed: {e}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e


def _load_json_schema(schema_file: str) -> dict[str, Any]:
    """Load a JSON schema from a file.
    
    Args:
        schema_file: Path to the JSON Schema file
        
    Returns:
        The loaded schema as a dictionary
        
    Raises:
        ConfigValidationError: If the schema file cannot be loaded
    """
    schema_path = pathlib.Path(schema_file)
    if not schema_path.exists():
        error_msg = f"Schema validation failed: Schema file '{schema_file}' not found."
        log.error(error_msg)
        raise ConfigValidationError(error_msg)
        
    # Parse schema file (support JSON only for JSON Schema spec compliance)
    try:
        if schema_file.lower().endswith('.json'):
            return cast(dict[str, Any], json.loads(schema_path.read_text()))
        else:
            error_msg = f"Schema validation failed: JSON Schema must be a .json file, got: {schema_file}"
            log.error(error_msg)
            raise ConfigValidationError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Schema validation failed: Invalid JSON in schema file '{schema_file}': {e}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e
    except Exception as e:
        error_msg = f"Schema validation failed: Error reading schema file '{schema_file}': {e}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e


def validate_config_with_jsonschema(config: dict[str, Any], schema_file: str) -> None:
    """Validate the final merged configuration against a JSON Schema.
    
    Args:
        config: The final merged configuration dictionary
        schema_file: Path to the JSON Schema file
        
    Raises:
        ConfigValidationError: If validation fails with detailed error message
    """
    try:
        schema = _load_json_schema(schema_file)
        
        # Validate the configuration
        jsonschema.validate(instance=config, schema=schema)
        print(f"✅ Configuration successfully validated against schema '{schema_file}'")
        
    except jsonschema.ValidationError as e:
        error_details = ["Schema validation failed:"]
        error_details.append(f"  Error at path: {' -> '.join(str(p) for p in e.absolute_path) if e.absolute_path else 'root'}")
        error_details.append(f"  Message: {e.message}")
        if e.validator_value:
            error_details.append(f"  Expected: {e.validator_value}")
        if hasattr(e, 'instance') and e.instance is not None:
            error_details.append(f"  Actual value: {e.instance}")
        error_details.append("  Full validation context:")
        error_details.append(f"  Schema rule: {e.validator} = {e.validator_value}")
        error_msg = "\n".join(error_details)
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e
    except jsonschema.SchemaError as e:
        error_msg = f"Schema validation failed: Invalid schema file. Schema error: {e.message}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e
    except ConfigValidationError:
        # Re-raise ConfigValidationError as-is
        raise
    except Exception as e:
        error_msg = f"Schema validation failed: {e}"
        log.error(error_msg)
        raise ConfigValidationError(error_msg) from e


def validate_config_with_schema(config: dict[str, Any], schema: str) -> None:
    """Validate the final merged configuration against a schema.
    
    Determines whether to use JSON Schema or Pydantic validation based on the schema format.
    
    Args:
        config: The final merged configuration dictionary
        schema: Either a path to a JSON Schema file or a Pydantic model spec (module.py::Model)
        
    Raises:
        ConfigValidationError: If validation fails with detailed error message
    """
    # Check if this is a Pydantic model specification (contains "::")
    if "::" in schema:
        # Pydantic validation - should be .py file
        module_path = schema.split("::", 1)[0]
        if not module_path.endswith('.py'):
            error_msg = f"Pydantic schema must be a .py file, got: {module_path}"
            log.error(error_msg)
            raise ConfigValidationError(error_msg)
        validate_config_with_pydantic(config, schema)
    else:
        # JSON Schema validation - should be .json file
        if not schema.endswith('.json'):
            error_msg = f"JSON Schema must be a .json file, got: {schema}"
            log.error(error_msg)
            raise ConfigValidationError(error_msg)
        validate_config_with_jsonschema(config, schema)


def _process_stdin_config(stdin_format: str | None, confs: list[dict[str, Any]]) -> None:
    """Process configuration from stdin if provided."""
    if stdin_format and not sys.stdin.isatty():
        log.debug(f"# Reading config from stdin with format: {stdin_format}")
        stdin_content = sys.stdin.read()
        if stdin_content.strip():  # Ensure content is not just whitespace
            try:
                stdin_conf = parse_stdin_content(stdin_content, stdin_format)
                if stdin_conf is not None:  # Check if parsing resulted in a valid (non-None) config
                    confs.append(stdin_conf)  # Add to the list of configs to be merged
                    log.debug(f"# Config from stdin: {json.dumps(stdin_conf, indent=2) if DEBUG_MODE else 'loaded'}")
                else:
                    log.debug("# stdin content parsed to None, not adding.")
            except Exception as e:
                log.error(f"Error parsing stdin content as {stdin_format}: {e}")
                # Optionally, re-raise or exit if stdin parsing is critical
        else:
            log.debug("# stdin was empty or whitespace only, no config read.")
    elif stdin_format and sys.stdin.isatty():
        log.debug(f"# --stdin-format '{stdin_format}' provided, but no data piped to stdin.")


def _write_output(output: str, final_conf: dict[str, Any], merged_template: str) -> None:
    """Write the final output based on the output format."""
    if output == "config-json":
        print(json.dumps(final_conf, indent=2))
    elif output in ("config-yaml", "config-yml"):
        print(yaml.dump(final_conf, indent=2))
    elif output == "stdout":
        print(merged_template)
    else:
        pathlib.Path(output).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(output).write_text(merged_template)


########################################################################################
# Main
########################################################################################
def merge(
    env: list[str] | None = None,
    config: list[str] | None = None,
    template: str = "",
    output: str = "stdout",
    validate: str | None = None,
    prefix: list[str] | None = None,
    functions: list[str] | None = None,
    stdin_format: str | None = None,  # Added stdin_format parameter
    schema: str | None = None,  # Added schema parameter
) -> tuple[str, str | None]:
    """Merge configuration files and Jinja2 template to produce a final configuration file.

    This is the programmatic interface to:
    
    - Take the DYNAMIC configuration (environment variables) and
    - merge it with the STATIC configuration (files) to produce a _final complex configuration_.
    - This final configuration is then applied to your target Jinja2 template file.

    OPTIONALLY:
    - Can take custom functions for use within the Jinja2 template engine.
    - Can take a validation file to assist with checking expected templated output against a known file.
    """
    # Defaults to empty lists (setting mutables as defaults is not recommended)
    _env: list[str] = env or []
    _config: list[str] = config or []
    _prefix: list[str] = prefix or []
    _functions: list[str] = functions or []
    
    # Dynamic configuration
    merged_env: dict[str, str] = get_environment_variables(env_flags=_env, prefixes_list=_prefix)
    
    # Custom functions
    log.debug(f"# functions {_functions=}")
    f = get_functions(_functions)
    TESTS.update(f["tests"])
    FILTERS.update(f["filters"])
    
    # Static configuration
    confs = map_env_to_confs(config_files_or_globs=_config, env=merged_env)
    log.debug(f"# confs: {json.dumps(confs, indent=2)}")
    
    # Process stdin configuration if provided
    _process_stdin_config(stdin_format, confs)
    
    final_conf = reduce_confs(confs)
    log.debug(f"# reduced confs: {json.dumps(final_conf, indent=2)}")
    
    # Validate final configuration against schema if provided
    if schema:
        try:
            validate_config_with_schema(final_conf, schema)
        except ConfigValidationError as e:
            log.error(str(e))
            sys.exit(1)
    
    merged_template = merge_template(template, final_conf) if template else ""
    log.debug(f"# merged_template: {merged_template=}")
    
    # Validation diff if requested
    diff = None
    if validate:
        validator_text = pathlib.Path(validate).read_text()
        diff = "\n".join(difflib.unified_diff(merged_template.splitlines(), validator_text.splitlines(), lineterm=""))
        log.debug(diff)
    
    # Write output in the requested format
    _write_output(output, final_conf, merged_template)
    
    return merged_template, diff


def main(_args: list[str] | None = None) -> None:
    """CLI entry point."""
    parser: argparse.ArgumentParser = __argparse_factory(CLI_CONFIG)
    args: dict[str, Any] = __handle_args(parser, _args)

    merge(
        env=args["env"],
        config=args["config"],
        template=args["template"],
        output=args["output"],
        validate=args["validate"],
        prefix=args["prefix"],
        functions=args["functions"],
        stdin_format=args["stdin_format"],
        schema=args["schema"],
    )


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=log_level, format=log_format, datefmt=log_date_format)
    main(sys.argv[1:])
