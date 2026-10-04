from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RiskCheckResult:
    """
    Unified result shape for any of the seven risk checks.
    This structure is stored as-is in the risk_checks table.
    """
    check_name: str          # "payment" / "fraud" / "stock" / ...
    passed: bool
    value: Decimal | None = None   # numeric value if applicable (e.g. margin %)
    reason: str | None = None      # short reason on failure, for audit purposes