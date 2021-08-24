import datetime
import time

import tabulate
from yaspin import yaspin

from colony.branch.branch_context import ContextBranch
from colony.branch.branch_utils import can_temp_branch_be_deleted, get_and_check_folder_based_repo, logger
from colony.commands.base import BaseCommand
from colony.constants import DEFAULT_TIMEOUT, FINAL_SB_STATUSES
from colony.parsers.command_input_validators import CommandInputValidator
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo


class SandboxesCommand(BaseCommand):
    """
    usage:
        colony (sb | sandbox) start <blueprint_name> [options]
        colony (sb | sandbox) status <sandbox_id>
        colony (sb | sandbox) end <sandbox_id>
        colony (sb | sandbox) list [--filter={all|my|auto}] [--show-ended] [--count=<N>]
        colony (sb | sandbox) [--help]

    options:
       -h --help                        Show this message
       -d, --duration <minutes>         The Sandbox will automatically de-provision at the end of the provided duration
       -n, --name <sandbox_name>        Provide a name for the Sandbox. If not set, the name will be generated
                                        automatically using the source branch (or local changes) and current time.

       -i, --inputs <input_params>      The Blueprints inputs can be provided as a comma-separated list of key=value
                                        pairs. For example: key1=value1, key2=value2.
                                        By default Colony CLI will try to take the default values for these inputs
                                        from the Blueprint definition yaml file.

       -a, --artifacts <artifacts>      A comma-separated list of artifacts per application. These are relative to the
                                        artifact repository root defined in Colony.
                                        Example: appName1=path1, appName2=path2.
                                        By default Colony CLI will try to take artifacts from blueprint definition yaml
                                        file.

       -b, --branch <branch>            Run the Blueprint version from a remote Git branch. If not provided,
                                        the CLI will attempt to automatically detect the current working branch.
                                        The CLI will automatically run any local uncommitted or untracked changes in a
                                        temporary branch created for the validation or for the development Sandbox.

       -c, --commit <commitId>          Specify a specific Commit ID. This is used in order to run a Sandbox from a
                                        specific Blueprint historic version. If this parameter is used, the
                                        Branch parameter must also be specified.

       -t, --timeout  <timeout>         Set the timeout in minutes to wait for the sandbox to become active. If not set,
                                        the CLI will wait for a default timeout of 30 minutes until the sandbox is
                                        ready.

       -w, --wait                       Wait for sandbox to finish launching process.


    """

    RESOURCE_MANAGER = SandboxesManager

    def get_actions_table(self) -> dict:
        return {"status": self.do_status, "start": self.do_start, "end": self.do_end, "list": self.do_list}

    def do_list(self):
        list_filter = self.input_parser.sandbox_list.filter
        show_ended = self.input_parser.sandbox_list.show_ended
        count = self.input_parser.sandbox_list.count

        try:
            sandbox_list = self.manager.list(filter_opt=list_filter, count=count)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        result_table = []
        for sb in sandbox_list:

            if sb.sandbox_status == "Ended" and not show_ended:
                continue

            result_table.append(
                {
                    "Sandbox ID": sb.sandbox_id,
                    "Sandbox Name": sb.name,
                    "Blueprint Name": sb.blueprint_name,
                    "Status": sb.sandbox_status,
                }
            )

        self.message(tabulate.tabulate(result_table, headers="keys"))

    def do_status(self):
        try:
            sandbox = self.manager.get(self.input_parser.sandbox_status.sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        status = getattr(sandbox, "sandbox_status")
        return self.success(status)

    def do_end(self):
        try:
            self.manager.end(self.input_parser.sandbox_status.sandbox_id)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        return self.success("End request has been sent")

    def do_start(self):
        # get commands inputs
        blueprint_name = self.input_parser.sandbox_start.blueprint_name
        branch = self.input_parser.sandbox_start.branch
        commit = self.input_parser.sandbox_start.commit
        sandbox_name = self.input_parser.sandbox_start.sandbox_name
        timeout = self.input_parser.sandbox_start.timeout
        wait = self.input_parser.sandbox_start.wait
        duration = self.input_parser.sandbox_start.duration
        inputs = self.input_parser.sandbox_start.inputs
        artifacts = self.input_parser.sandbox_start.artifacts
        repo = get_and_check_folder_based_repo(blueprint_name)
        self._update_missing_artifacts_and_inputs_with_default_values(artifacts, blueprint_name, inputs, repo)

        CommandInputValidator.validate_commit_and_branch_specified(branch, commit)
        with ContextBranch(repo, branch) as context_branch:
            # TODO move error handling to exception catch (investigate best practices of error handling)
            if not context_branch:
                return self.error("Unable to start Sandbox")

            if sandbox_name is None:
                sandbox_name_input = self.generate_sandbox_name(
                    blueprint_name,
                    context_branch.temp_working_branch,
                    context_branch.working_branch,
                )

            try:
                sandbox_id = self.manager.start(
                    sandbox_name_input,
                    blueprint_name,
                    duration,
                    context_branch.validation_branch,
                    commit,
                    artifacts,
                    inputs,
                )
                BaseCommand.action_announcement("Starting sandbox")
                BaseCommand.important_value("Id: ", sandbox_id)
                BaseCommand.url(prefix_message="URL: ", message=self.manager.get_sandbox_ui_link(sandbox_id))

            except Exception as e:
                logger.exception(e, exc_info=False)
                return self.die()

            wait_timeout_reached = wait_for_sandbox_to_launch(
                self.manager,
                sandbox_id,
                timeout,
                context_branch,
                wait
            )

            if wait_timeout_reached:
                return self.die()
            else:
                return self.success(sandbox_id)

    def _update_missing_artifacts_and_inputs_with_default_values(self, artifacts, blueprint_name, inputs, repo):
        # TODO(ddovbii): This obtaining default values magic must be refactored
        logger.debug("Trying to obtain default values for artifacts and inputs from local git blueprint repo")
        try:
            if not repo.is_current_branch_synced():
                logger.debug("Skipping obtaining values since local branch is not synced with remote")
            else:
                for art_name, art_path in repo.get_blueprint_artifacts(blueprint_name).items():
                    if art_name not in artifacts and art_path is not None:
                        logger.debug(f"Artifact `{art_name}` has been set with default path `{art_path}`")
                        artifacts[art_name] = art_path

                for input_name, input_value in repo.get_blueprint_default_inputs(blueprint_name).items():
                    if input_name not in inputs and input_value is not None:
                        logger.debug(f"Parameter `{input_name}` has been set with default value `{input_value}`")
                        inputs[input_name] = input_value

        except Exception as e:
            logger.debug(f"Unable to obtain default values. Details: {e}")
        return repo

    def generate_sandbox_name(self, blueprint_name: str, temp_working_branch: str, working_branch: str) -> str:
        suffix = datetime.datetime.now().strftime("%b%d-%H:%M:%S")
        branch_name_or_type = ""
        if working_branch:
            branch_name_or_type = working_branch + "-"
        if temp_working_branch:
            branch_name_or_type = "localchanges-"
        return f"{blueprint_name}-{branch_name_or_type}{suffix}"


def wait_for_sandbox_to_launch(
    sb_manager: SandboxesManager,
    sandbox_id: str,
    timeout: int,
    context_branch: ContextBranch,
    wait: bool,
) -> bool:

    if not wait and not context_branch.temp_branch_exists:
        return False
    try:
        if context_branch.temp_branch_exists:
            context_branch.revert_from_local_temp_branch()

        if not timeout:
            timeout = DEFAULT_TIMEOUT

        start_time = datetime.datetime.now()
        sandbox = sb_manager.get(sandbox_id)
        status = getattr(sandbox, "sandbox_status")

        sandbox_start_wait_output(sandbox_id, context_branch.temp_branch_exists)

        with yaspin(text="Starting...", color="yellow") as spinner:
            while (datetime.datetime.now() - start_time).seconds < timeout * 60:
                if status in FINAL_SB_STATUSES:
                    spinner.green.ok("✔")
                    break
                if context_branch.temp_branch_exists and can_temp_branch_be_deleted(sandbox):
                    context_branch.delete_temp_branch()
                    if not wait:
                        spinner.green.ok("✔")
                        break

                time.sleep(10)
                spinner.text = f"[{int((datetime.datetime.now() - start_time).total_seconds())} sec]"
                sandbox = sb_manager.get(sandbox_id)
                status = getattr(sandbox, "sandbox_status")
            else:
                logger.error(f"Timeout Reached - Sandbox {sandbox_id} was not active after {timeout} minutes")
                return True
        return False

    except Exception as e:
        logger.error(f"There was an issue with waiting for sandbox deployment -> {str(e)}")


def sandbox_start_wait_output(sandbox_id, temp_branch_exists):
    if temp_branch_exists:
        logger.debug(f"Waiting before deleting temp branch that was created for this sandbox (id={sandbox_id})")
        BaseCommand.fyi_info("Canceling or exiting before the process completes may cause the sandbox to fail")
        BaseCommand.info("Waiting for the Sandbox to start with local changes. This may take some time.")
    else:
        logger.debug(f"Waiting for the Sandbox {sandbox_id} to finish launching...")
        BaseCommand.info("Waiting for the Sandbox to start. This may take some time.")
