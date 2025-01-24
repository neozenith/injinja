# ruff: noqa: E501
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2",
#   "PyYAML",
#   "types-PyYAML",
#   "deepmerge",
# ]
# ///
# https://docs.astral.sh/uv/guides/scripts/#creating-a-python-script
# https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata


# Standard Library
import argparse
import difflib
import glob
import itertools
import json
import logging
import pathlib
import sys
import tomllib
from typing import Any

# Third Party
import jinja2
import yaml
from deepmerge import always_merger

log = logging.getLogger(__name__)

log_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
logging.basicConfig(level=log_level, format="%(message)s")
log.debug(f"# {sys.argv}")
log.debug(f"# {pathlib.Path.cwd()}")

cli_config = {
    "debug": True,
    "template": {"required": True, "help": "The Jinja2 template file to use."},
    "config": {
        "required": True,
        "default": [],
        "action": "append",
        "help": """
               The configuration file(s) to use. 
               Either specify a single file, repeated config flags for multiple files or a glob pattern.
        """,
    },
    "env": {"action": "append", "default": [], "help": "Environment variables to pass to the template."},
    "validate": {"help": "Filename of an outputfile to validate the output against."},
    "output": "stdout",
}


def __argparse_factory(config):
    """Josh's Opinionated Argument Parser Factory."""
    parser = argparse.ArgumentParser()

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


def __handle_args(parser, args):
    script_filename = pathlib.Path(__file__).name
    # log.info(script_filename)
    if script_filename in args:
        args.remove(script_filename)
    return vars(parser.parse_args(args))


def __expand_files_list(file_or_glob: str) -> list[str]:
    """Get a list of files from a glob pattern."""
    if pathlib.Path(file_or_glob).is_file():
        return [file_or_glob]
    return glob.glob(file_or_glob)


def dict_from_keyvalue_list(args: list[str] | None = None) -> dict[str, str] | None:
    """Convert a list of 'key=value' strings into a dictionary."""
    return {k: v for k, v in [x.split("=") for x in args]} if args else None


def merge_template(template_filename: str, config: dict[str, Any] | None) -> str:
    """Load a Jinja2 template from file and merge configuration."""
    # Step 1: get raw content as a string
    raw_content = pathlib.Path(template_filename).read_text()

    # Step 2: Treat raw_content as a Jinja2 template if providing configuration
    if config:
        # NOTE: Providing jinja 2.11.x compatable version to better cross operate
        # with dbt-databricks v1.2.2 and down stream dbt-spark and dbt-core
        if int(jinja2.__version__[0]) >= 3:
            content = jinja2.Template(raw_content, undefined=jinja2.StrictUndefined).render(**config)
        else:
            content = jinja2.Template(raw_content).render(**config)

    else:
        content = raw_content

    return content


def load_config(filename: str, environment_variables: dict[str, str] | None = None) -> Any:
    """Detect if file is JSON or YAML and return parsed datastructure.

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


def main(args):
    parser = __argparse_factory(cli_config)
    args = __handle_args(parser, sys.argv)
    env = dict_from_keyvalue_list(args["env"])
    log.debug(f"# env: {env=}")
    log.debug(f"# config sources: {args["config"]=}")

    all_conf_files = list(itertools.chain.from_iterable([__expand_files_list(x) for x in args["config"]]))

    log.debug(f"# all_conf_files: {all_conf_files=}")
    confs = [load_config(conf, env) for conf in all_conf_files]
    log.debug(f"# confs: {confs=}")
    final_conf = {}
    for conf in confs:
        always_merger.merge(final_conf, conf)
    log.debug(f"# final_conf: {final_conf=}")
    merged_template = merge_template(args["template"], final_conf)
    log.debug(f"# merged_template: {merged_template=}")

    if args["validate"]:
        validator_text = pathlib.Path(args["validate"]).read_text()
        diff = "\n".join(difflib.unified_diff(merged_template.splitlines(), validator_text.splitlines(), lineterm=""))
        log.debug(diff)

    if args["output"] == "stdout":
        print(merged_template)
    else:
        pathlib.Path(args["output"]).write_text(merged_template)


if __name__ == "__main__":
    main(sys.argv)
