"""Optional attribution for a newly calculated target; no retrofit of old targets."""

from datetime import datetime
import re

FIELDS = {"schema_version", "method", "model_version", "table_id", "source_url",
          "table_sha256", "calculated_at_local", "target_iso"}


def validate_provenance(value, target_iso):
    """Check imported metadata's shape and target binding, not its authenticity."""
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Invalid calculation details in this file.")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("Unsupported calculation-details version.")
    if any(not isinstance(value[key], str) or not 1 <= len(value[key]) <= 2048
           for key in FIELDS - {"schema_version"}):
        raise ValueError("Invalid calculation details in this file.")
    if (value["method"] != "legacy_calculation" or value["target_iso"] != target_iso
            or re.fullmatch(r"[0-9a-f]{64}", value["table_sha256"]) is None
            or not value["source_url"].startswith("https://www.ssa.gov/")):
        raise ValueError("Calculation details do not match the saved target or source format.")
    try:
        datetime.fromisoformat(value["calculated_at_local"])
    except ValueError:
        raise ValueError("Invalid calculation date in this file.") from None
