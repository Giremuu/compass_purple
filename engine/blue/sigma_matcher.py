import re
from pathlib import Path

import paramiko
import yaml

from engine.base import BlueModule

SIGMA_RULES_PATH = Path(__file__).parents[2] / "data" / "sigma" / "rules"


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# --- Rule loading ---

def list_rules(platform: str = "linux", category: str | None = None) -> list[dict]:
    """Return all Sigma rules for a given platform and optional category."""
    base = SIGMA_RULES_PATH / platform
    if not base.exists():
        return []

    search_path = base / category if category else base
    rules = []
    for path in search_path.rglob("*.yml"):
        try:
            data = _load_yaml(path)
            rules.append({
                "id": data.get("id", ""),
                "title": data.get("title", ""),
                "status": data.get("status", ""),
                "level": data.get("level", ""),
                "tags": data.get("tags", []),
                "description": data.get("description", ""),
                "file": str(path.relative_to(SIGMA_RULES_PATH)),
            })
        except Exception:
            continue
    return rules


def load_rule(rule_file: str) -> dict | None:
    """Load a full Sigma rule by its relative file path."""
    path = SIGMA_RULES_PATH / rule_file
    if not path.exists():
        return None
    return _load_yaml(path)


# --- Detection engine ---

def _match_value(value: str, modifier: str | None, field_value: str) -> bool:
    """Apply a Sigma modifier to compare a rule value against a log field value."""
    if not isinstance(field_value, str):
        field_value = str(field_value)
    if modifier == "endswith":
        return field_value.endswith(value)
    if modifier == "startswith":
        return field_value.startswith(value)
    if modifier == "contains":
        return value in field_value
    if modifier == "re":
        return bool(re.search(value, field_value))
    return field_value == value


def _match_field(field_expr: str, rule_values, log_entry: dict) -> bool:
    """
    Match a Sigma field expression (e.g. 'Image|endswith') against a log entry dict.
    rule_values can be a single value or a list (OR logic).
    """
    parts = field_expr.split("|")
    field = parts[0]
    modifier = parts[1] if len(parts) > 1 else None

    log_value = log_entry.get(field)
    if log_value is None:
        return False

    values = rule_values if isinstance(rule_values, list) else [rule_values]
    return any(_match_value(str(v), modifier, str(log_value)) for v in values)


def _evaluate_selection(selection: dict, log_entry: dict) -> bool:
    """All fields in a selection must match (AND logic)."""
    return all(_match_field(field, values, log_entry) for field, values in selection.items())


def _evaluate_condition(condition: str, selections: dict, log_entry: dict) -> bool:
    """
    Evaluate a Sigma condition string against evaluated selections.
    Supports: '1 of selection_*', 'all of selection_*', 'selectionA and selectionB', 'selectionA or selectionB'.
    """
    results = {name: _evaluate_selection(sel, log_entry) for name, sel in selections.items()}

    # "1 of selection_*"
    if re.match(r"1 of selection_\*", condition):
        return any(results.values())

    # "all of selection_*"
    if re.match(r"all of selection_\*", condition):
        return all(results.values())

    # "1 of them"
    if condition.strip() == "1 of them":
        return any(results.values())

    # "all of them"
    if condition.strip() == "all of them":
        return all(results.values())

    # Replace selection names with their boolean results
    expr = condition
    for name, result in results.items():
        expr = expr.replace(name, str(result))
    expr = expr.replace(" and ", " and ").replace(" or ", " or ").replace("not ", "not ")

    try:
        return bool(eval(expr))  # noqa: S307 — controlled input from Sigma rule files
    except Exception:
        return False


def match_rule(rule: dict, log_entries: list[dict]) -> list[dict]:
    """
    Match a Sigma rule against a list of log entries.
    Returns matching log entries.
    """
    detection = rule.get("detection", {})
    condition = detection.get("condition", "")
    selections = {k: v for k, v in detection.items() if k != "condition"}

    matches = []
    for entry in log_entries:
        if _evaluate_condition(condition, selections, entry):
            matches.append(entry)
    return matches


# --- Log collection ---

def _collect_logs_ssh(target: dict, log_paths: list[str]) -> list[dict]:
    """Fetch log lines from a remote target via SSH. Returns structured log entries."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    entries = []
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

        for log_path in log_paths:
            _, stdout, _ = client.exec_command(f"tail -n 500 {log_path} 2>/dev/null")
            for line in stdout.read().decode(errors="replace").splitlines():
                entries.append({"raw": line, "CommandLine": line, "log_path": log_path})
    except Exception as e:
        entries.append({"error": str(e)})
    finally:
        client.close()
    return entries


# --- Module ---

class SigmaMatcherModule(BlueModule):
    name = "sigma_matcher"
    description = "Match Sigma rules against logs collected from a target"
    version = "1.0.0"

    def run(self, params: dict) -> dict:
        """
        params:
          - action: "list_rules" | "match"
          - platform: "linux" / "windows" / ...        (for list_rules)
          - category: "process_creation" / ...          (for list_rules, optional)
          - rule_file: relative path to a .yml rule     (for match)
          - log_entries: list of dicts                  (for match, manual input)
          - target: {host, port, username, ...}         (for match, collect logs via SSH)
          - log_paths: list of paths to collect         (for match with target)
        """
        action = params.get("action", "list_rules")

        if action == "list_rules":
            platform = params.get("platform", "linux")
            category = params.get("category")
            return {"status": "success", "rules": list_rules(platform, category)}

        if action == "match":
            return self._match(params)

        return {"status": "error", "message": f"Unknown action: {action}"}

    def _match(self, params: dict) -> dict:
        rule_file = params.get("rule_file")
        if not rule_file:
            return {"status": "error", "message": "rule_file is required"}

        rule = load_rule(rule_file)
        if not rule:
            return {"status": "error", "message": f"Rule '{rule_file}' not found"}

        # Get log entries: from SSH target or provided directly
        target = params.get("target")
        if target:
            log_paths = params.get("log_paths", ["/var/log/syslog", "/var/log/auth.log"])
            log_entries = _collect_logs_ssh(target, log_paths)
        else:
            log_entries = params.get("log_entries", [])

        if not log_entries:
            return {"status": "error", "message": "No log entries to match against"}

        matches = match_rule(rule, log_entries)
        return {
            "status": "success",
            "rule_title": rule.get("title"),
            "rule_id": rule.get("id"),
            "total_entries": len(log_entries),
            "matches": len(matches),
            "matched_entries": matches[:50],  # cap at 50 to avoid huge responses
        }
