import subprocess
from pathlib import Path

import paramiko
import yaml

from engine.base import RedModule

ATOMICS_PATH = Path(__file__).parents[2] / "data" / "atomic" / "atomics"
INDEXES_PATH = ATOMICS_PATH / "Indexes"

PLATFORM_INDEXES = {
    "linux": "linux-index.yaml",
    "windows": "windows-index.yaml",
    "macos": "macos-index.yaml",
}


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_input_args(command: str, input_arguments: dict) -> str:
    """Replace #{arg_name} placeholders with their default values."""
    for arg_name, arg_data in input_arguments.items():
        default = str(arg_data.get("default", ""))
        command = command.replace(f"#{{{arg_name}}}", default)
    return command


def list_techniques(platform: str = "linux") -> list[dict]:
    """Return all techniques available for a given platform."""
    index_file = INDEXES_PATH / PLATFORM_INDEXES.get(platform, "linux-index.yaml")
    index = _load_yaml(index_file)

    techniques = []
    for tactic, tactic_techniques in index.items():
        for technique_id, technique_data in tactic_techniques.items():
            techniques.append({
                "id": technique_id,
                "name": technique_data.get("technique", {}).get("name", ""),
                "tactic": tactic,
                "platform": platform,
            })
    return techniques


def get_technique(technique_id: str) -> dict | None:
    """Parse and return a technique's YAML file with all its atomic tests."""
    yaml_path = ATOMICS_PATH / technique_id / f"{technique_id}.yaml"
    if not yaml_path.exists():
        return None
    return _load_yaml(yaml_path)


def _run_local(command: str, executor_name: str) -> dict:
    """Execute a command on the local machine."""
    shell_map = {
        "sh": ["sh", "-c"],
        "bash": ["bash", "-c"],
        "command_prompt": ["sh", "-c"],
        "powershell": ["sh", "-c"],
    }
    shell = shell_map.get(executor_name, ["sh", "-c"])
    try:
        result = subprocess.run(shell + [command], capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (30s)"}


def _run_ssh(command: str, target: dict) -> dict:
    """Execute a command on a remote target via SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connect_kwargs = {
            "hostname": target["host"],
            "port": target.get("port", 22),
            "username": target["username"],
            "timeout": 30,
        }
        if target.get("ssh_key_path"):
            connect_kwargs["key_filename"] = target["ssh_key_path"]
        elif target.get("password"):
            connect_kwargs["password"] = target["password"]

        client.connect(**connect_kwargs)
        _, stdout, stderr = client.exec_command(command, timeout=30)
        return {
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
            "returncode": stdout.channel.recv_exit_status(),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        client.close()


class AtomicRedTeamModule(RedModule):
    name = "atomic_redteam"
    description = "Run Atomic Red Team tests against a target"
    version = "1.0.0"

    def run(self, params: dict) -> dict:
        """
        params:
          - action: "list" | "get" | "execute"
          - platform: "linux" | "windows" | "macos"    (for list)
          - technique_id: e.g. "T1057"                 (for get / execute)
          - test_index: int (0-based)                   (for execute)
          - input_args: dict of overrides               (for execute, optional)
          - target: {host, port, username, password, ssh_key_path}  (optional — local if absent)
        """
        action = params.get("action", "list")

        if action == "list":
            platform = params.get("platform", "linux")
            return {"status": "success", "techniques": list_techniques(platform)}

        if action == "get":
            technique_id = params.get("technique_id")
            if not technique_id:
                return {"status": "error", "message": "technique_id is required"}
            data = get_technique(technique_id)
            if not data:
                return {"status": "error", "message": f"Technique {technique_id} not found"}
            return {"status": "success", "technique": data}

        if action == "execute":
            return self._execute(params)

        return {"status": "error", "message": f"Unknown action: {action}"}

    def _execute(self, params: dict) -> dict:
        technique_id = params.get("technique_id")
        test_index = params.get("test_index", 0)
        input_overrides = params.get("input_args", {})
        target = params.get("target")  # None = execute locally

        if not technique_id:
            return {"status": "error", "message": "technique_id is required"}

        data = get_technique(technique_id)
        if not data:
            return {"status": "error", "message": f"Technique {technique_id} not found"}

        tests = data.get("atomic_tests", [])
        if test_index >= len(tests):
            return {"status": "error", "message": f"test_index {test_index} out of range"}

        test = tests[test_index]
        executor = test.get("executor", {})
        command = executor.get("command", "")
        executor_name = executor.get("name", "sh")

        if not command:
            return {"status": "error", "message": "No command defined for this test"}

        input_arguments = test.get("input_arguments", {})
        for key, value in input_overrides.items():
            if key in input_arguments:
                input_arguments[key]["default"] = value
        command = _resolve_input_args(command, input_arguments)

        if target:
            exec_result = _run_ssh(command, target)
        else:
            exec_result = _run_local(command, executor_name)

        if "error" in exec_result:
            return {"status": "error", "message": exec_result["error"]}

        return {
            "status": "success",
            "technique_id": technique_id,
            "test_name": test.get("name"),
            "executor": executor_name,
            "target": target.get("host") if target else "local",
            **exec_result,
        }
