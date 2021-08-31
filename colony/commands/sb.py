import tabulate

from colony.branch.branch_context import ContextBranch
from colony.branch.branch_utils import get_and_check_folder_based_repo, logger
from colony.commands.base import BaseCommand
from colony.parsers.command_input_validators import CommandInputValidator
from colony.sandboxes import SandboxesManager
from colony.services.sb_naming import generate_sandbox_name
from colony.services.waiter import Waiter


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

       -t, --timeout <minutes>          Set how long (default timeout is 30 minutes) to block and wait before releasing
                                        control back to shell prompt. If timeout is reached before the desired status
                                        the wait loop will be interrupted.
                                        If "wait_active" flag is not set and a temp branch is created for local changes,
                                        the CLI will block and wait until the sandbox Infrastructure and Artifacts are
                                        ready. Then the temp branch can be safely deleted and the wait loop will end.
                                        If "wait_active" flag is set, the CLI will block and wait until the sandbox is
                                        Active regardless if temp branch is created or not.

       -w, --wait_active                Block shell prompt and wait for the sandbox to be Active (or deployment ended
                                        with an error) while the timeout is not reached. Default timeout is 30 minutes.
                                        The default timeout can be changed using the "timeout" flag.


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
        CommandInputValidator.validate_commit_and_branch_specified(branch, commit)

        sandbox_name = self.input_parser.sandbox_start.sandbox_name
        timeout = self.input_parser.sandbox_start.timeout
        wait = self.input_parser.sandbox_start.wait
        duration = self.input_parser.sandbox_start.duration
        inputs = self.input_parser.sandbox_start.inputs
        artifacts = self.input_parser.sandbox_start.artifacts

        repo = get_and_check_folder_based_repo(blueprint_name)
        self._update_missing_artifacts_and_inputs_with_default_values(artifacts, blueprint_name, inputs, repo)

        with ContextBranch(repo, branch) as context_branch:
            # TODO move error handling to exception catch (investigate best practices of error handling)

            if sandbox_name is None:
                sandbox_name_input = generate_sandbox_name(
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

            wait_timeout_reached = Waiter.wait_for_sandbox_to_launch(
                self.manager, sandbox_id, timeout, context_branch, wait
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
