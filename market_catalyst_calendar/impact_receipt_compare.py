"""Compare impact artifact receipt outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


LIMITATIONS = [
    "Static receipt comparison only: inputs are existing local JSON receipts and no market, news, or broker data is fetched.",
    "Non-advisory evidence: output reports artifact drift and does not recommend trades, positions, or investment actions.",
    "Hash-based artifact drift: changed entries are based on receipt metadata such as schema labels, bytes, hashes, and rerun commands.",
]


def impact_receipt_compare_json(
    base: Mapping[str, Any],
    current: Mapping[str, Any],
    base_path: str,
    current_path: str,
) -> Dict[str, object]:
    """Return deterministic drift evidence between two impact artifact receipts."""

    _validate_receipt(base, "base")
    _validate_receipt(current, "current")
    base_items = _artifacts_by_path(base)
    current_items = _artifacts_by_path(current)
    base_paths = set(base_items)
    current_paths = set(current_items)

    added = {path: _artifact_summary(current_items[path]) for path in sorted(current_paths - base_paths)}
    removed = {path: _artifact_summary(base_items[path]) for path in sorted(base_paths - current_paths)}
    changed: Dict[str, object] = {}
    unchanged: Dict[str, object] = {}
    for path in sorted(base_paths & current_paths):
        diff = _artifact_diff(base_items[path], current_items[path])
        if diff["changed_fields"]:
            changed[path] = diff
        else:
            unchanged[path] = _artifact_summary(current_items[path])

    boundary = _boundary_check(base, current)
    return {
        "schema_version": "impact-receipt-compare/v1",
        "base_path": base_path,
        "current_path": current_path,
        "base_schema_version": str(base.get("schema_version", "")),
        "current_schema_version": str(current.get("schema_version", "")),
        "ok": not changed and not added and not removed and boundary["matches"],
        "summary": {
            "base_artifact_count": len(base_items),
            "current_artifact_count": len(current_items),
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "unchanged_count": len(unchanged),
            "boundary_match": boundary["matches"],
        },
        "boundary": boundary,
        "limitations": LIMITATIONS,
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def impact_receipt_compare_markdown(payload: Mapping[str, Any]) -> str:
    """Render receipt drift evidence as Markdown."""

    summary = payload["summary"]
    lines = [
        "# Market Catalyst Impact Receipt Compare",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Status: {'PASS' if payload['ok'] else 'DRIFT'}",
        f"Base: `{payload['base_path']}`",
        f"Current: `{payload['current_path']}`",
        "",
        (
            "Summary: "
            f"{summary['added_count']} added, "
            f"{summary['removed_count']} removed, "
            f"{summary['changed_count']} changed, "
            f"{summary['unchanged_count']} unchanged; "
            f"boundaries {'match' if summary['boundary_match'] else 'differ'}."
        ),
        "",
        "## Limitations",
        "",
    ]
    for limitation in payload["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Boundary Check",
            "",
            "| Check | Result |",
            "| --- | --- |",
        ]
    )
    boundary = payload["boundary"]
    lines.append(f"| base receipt ok | {_cell(str(boundary['base_ok']))} |")
    lines.append(f"| current receipt ok | {_cell(str(boundary['current_ok']))} |")
    lines.append(f"| boundary text match | {_cell(str(boundary['matches']))} |")
    _append_table(lines, "Added Artifacts", payload["added"])
    _append_table(lines, "Removed Artifacts", payload["removed"])
    _append_changed_table(lines, payload["changed"])
    _append_table(lines, "Unchanged Artifacts", payload["unchanged"])
    return "\n".join(lines).rstrip() + "\n"


def _validate_receipt(receipt: Mapping[str, Any], label: str) -> None:
    if receipt.get("schema_version") != "impact-artifact-receipt/v1":
        raise ValueError(f"{label} must be an impact-artifact-receipt/v1 JSON object")
    if not isinstance(receipt.get("artifacts"), list):
        raise ValueError(f"{label} receipt artifacts must be a list")


def _artifacts_by_path(receipt: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    artifacts: Dict[str, Mapping[str, Any]] = {}
    for raw in receipt["artifacts"]:
        if not isinstance(raw, Mapping):
            raise ValueError("receipt artifacts must be objects")
        path = str(raw.get("output_path") or raw.get("name") or "")
        if not path:
            raise ValueError("receipt artifacts must include output_path or name")
        if path in artifacts:
            raise ValueError(f"receipt artifacts must have unique output_path or name values: {path}")
        artifacts[path] = raw
    return artifacts


def _artifact_summary(artifact: Mapping[str, Any]) -> Dict[str, object]:
    return {
        "name": str(artifact.get("name", "")),
        "format": str(artifact.get("format", "")),
        "schema_label": str(artifact.get("schema_label", "")),
        "present": bool(artifact.get("present", False)),
        "bytes": int(artifact.get("bytes", 0) or 0),
        "sha256": artifact.get("sha256"),
        "rerun_command": str(artifact.get("rerun_command", "")),
    }


def _artifact_diff(base: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, object]:
    fields = ["name", "format", "schema_label", "present", "bytes", "sha256", "rerun_command"]
    changes = []
    for field in fields:
        if base.get(field) != current.get(field):
            changes.append({"field": field, "base": base.get(field), "current": current.get(field)})
    return {
        "base": _artifact_summary(base),
        "current": _artifact_summary(current),
        "changed_fields": changes,
    }


def _boundary_check(base: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, object]:
    base_boundaries = [str(item) for item in _list_value(base.get("boundaries"))]
    current_boundaries = [str(item) for item in _list_value(current.get("boundaries"))]
    return {
        "base_ok": bool(base.get("ok", False)),
        "current_ok": bool(current.get("ok", False)),
        "base_boundaries": base_boundaries,
        "current_boundaries": current_boundaries,
        "matches": base_boundaries == current_boundaries,
    }


def _list_value(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _append_table(lines: List[str], title: str, items: Mapping[str, Any]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not items:
        lines.extend([f"No {title.lower()}.", ""])
        return
    lines.extend(["| Artifact | Schema | Bytes | SHA-256 | Rerun |", "| --- | --- | ---: | --- | --- |"])
    for path, item in items.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(path),
                    _cell(str(item.get("schema_label", ""))),
                    _cell(str(item.get("bytes", 0))),
                    _cell(str(item.get("sha256") or "")),
                    _cell(str(item.get("rerun_command", ""))),
                ]
            )
            + " |"
        )
    lines.append("")


def _append_changed_table(lines: List[str], items: Mapping[str, Any]) -> None:
    lines.extend(["", "## Changed Artifacts", ""])
    if not items:
        lines.extend(["No changed artifacts.", ""])
        return
    lines.extend(["| Artifact | Fields | Base SHA-256 | Current SHA-256 |", "| --- | --- | --- | --- |"])
    for path, item in items.items():
        fields = ", ".join(str(change["field"]) for change in item["changed_fields"])
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(path),
                    _cell(fields),
                    _cell(str(item["base"].get("sha256") or "")),
                    _cell(str(item["current"].get("sha256") or "")),
                ]
            )
            + " |"
        )
    lines.append("")


def _cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")
