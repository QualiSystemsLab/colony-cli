from abc import ABC
from typing import Dict

from colony.parsers.command_input_validators import SandboxListValidator, SandboxStartInputValidator
from colony.utils import parse_comma_separated_string


class CommandInputParser:
    def __init__(self, command_args: Dict):
        """
        Parses CLI args for inputs that appear after the command
        :param command_args: command_args is expected to be initialized using doc_opt
        """
        self.sandbox_start = SandboxStartInputParser(command_args)
        self.sandbox_list = SandboxListInputParser(command_args)
        self.sandbox_end = SandboxEndInputParser(command_args)
        self.sandbox_status = SandboxStatusInputParser(command_args)
        self.blueprint_validate = BlueprintValidateInputParser(command_args)
        self.configure_remove = ConfigureRemoveInputParser(command_args)


class InputParserBase(ABC):
    def __init__(self, command_args: Dict):
        self._args = command_args


class ConfigureRemoveInputParser(InputParserBase):
    @property
    def profile(self) -> str:
        return self._args["<profile>"]


class BlueprintValidateInputParser(InputParserBase):
    @property
    def blueprint_name(self) -> str:
        return self._args.get("<name>")

    @property
    def branch(self) -> str:
        return self._args.get("--branch")

    @property
    def commit(self) -> str:
        return self._args.get("--commit")


class SandboxEndInputParser(InputParserBase):
    @property
    def sandbox_id(self) -> str:
        return self._args["<sandbox_id>"]


class SandboxStatusInputParser(InputParserBase):
    @property
    def sandbox_id(self) -> str:
        return self._args["<sandbox_id>"]


class SandboxListInputParser(InputParserBase):
    @property
    def filter(self) -> str:
        list_filter = self._args.get("--filter", "my")
        if not list_filter:
            list_filter = "my"
        SandboxListValidator.validate_filter(list_filter)
        return list_filter

    @property
    def show_ended(self) -> bool:
        return self._args["--show-ended"]

    @property
    def count(self) -> int:
        return self._args.get("--count", 25)

    # @property
    # def sandbox_id(self) -> str:
    #     return self._args["<sandbox_id>"]


class SandboxStartInputParser(InputParserBase):
    @property
    def blueprint_name(self) -> str:
        return self._args["<blueprint_name>"]

    @property
    def branch(self) -> str:
        return self._args.get("--branch")

    @property
    def commit(self) -> str:
        return self._args.get("--commit")

    @property
    def sandbox_name(self) -> str:
        return self._args["--name"]

    @property
    def wait(self) -> bool:
        return self._args["--wait_active"]

    @property
    def timeout(self) -> int:
        timeout = self._args["--timeout"]
        SandboxStartInputValidator.validate_timeout(timeout)
        return int(timeout) if timeout is not None else timeout

    @property
    def duration(self) -> int:
        duration = self._args["--duration"]
        SandboxStartInputValidator.validate_duration(duration)
        return int(duration or 120)

    @property
    def inputs(self) -> dict:
        return parse_comma_separated_string(self._args["--inputs"])

    @property
    def artifacts(self) -> dict:
        return parse_comma_separated_string(self._args["--artifacts"])
