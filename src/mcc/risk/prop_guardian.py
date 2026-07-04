"""PropGuardian for drawdown/LOCKOUT."""
from decimal import Decimal
from enum import Enum

class RiskLevel(str, Enum):
    OK = "OK"
    CAUTION = "CAUTION"
    LOCKOUT = "LOCKOUT"

def get_risk_level(headroom: Decimal, daily_loss: Decimal) -> RiskLevel:
    if headroom < Decimal('0.1') or daily_loss < Decimal('-0.03'):
        return RiskLevel.LOCKOUT
    if headroom < Decimal('0.3'):
        return RiskLevel.CAUTION
    return RiskLevel.OK
