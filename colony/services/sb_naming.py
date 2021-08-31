import datetime


def generate_sandbox_name(blueprint_name: str, temp_working_branch: str, working_branch: str) -> str:
    suffix = datetime.datetime.now().strftime("%b%d-%H:%M:%S")
    branch_name_or_type = ""
    if working_branch:
        branch_name_or_type = working_branch + "-"
    if temp_working_branch:
        branch_name_or_type = "localchanges-"
    return f"{blueprint_name}-{branch_name_or_type}{suffix}"
