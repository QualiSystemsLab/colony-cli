from typing import Dict, List

from docopt import DocoptExit


class CommandInputValidator:
    @staticmethod
    def validate_sandbox_list_filter(value):
        if value not in ["my", "all", "auto"]:
            raise DocoptExit("--filter value must be in [my, all, auto]")


class CommandInputParser:
    def __init__(self, command_args: Dict):
        """
        Parses CLI args for inputs that appear after the command
        :param command_args: command_args is expected to be initialized using doc_opt
        """
        self._args = command_args

    @property
    def sandbox_list_filter(self) -> str:
        list_filter = self._args.get("--filter", "my")
        CommandInputValidator.validate_sandbox_list_filter(list_filter)
        return list_filter

    @property
    def sandbox_list_show_ended(self) -> bool:
        return self._args["--show-ended"]

    @property
    def sandbox_list_count(self) -> int:
        return self._args.get("--count", 25)

    @property
    def sandbox_id(self) -> str:
        return self._args["<sandbox_id>"]

    @property
    def sandbox_start_blueprint_name(self) -> str:
        return self._args["<blueprint_name>"]

    @property
    def sandbox_start_branch(self) -> str:
        return self._args.get("--branch")

    @property
    def sandbox_start_commit(self) -> str:
        return self._args.get("--commit")

    @property
    def sandbox_start_sandbox_name(self) -> str:
        return self._args["--name"]

    @property
    def sandbox_start_wait(self) -> str:
        return self._args["--wait"]


    @property
    def sandbox_start_inputs(self) -> str:
        return self.args["--inputs"]

    @property
    def sandbox_start_artifacts(self) -> str:
        return self.args["--artifacts"]

