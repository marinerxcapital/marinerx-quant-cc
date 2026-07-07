from marinerx_tradeify.eval_engine import evaluate_select_150k_eval
from marinerx_tradeify.models import AccountPhase, AccountSnapshot, DayResult, SignalIntent, TradeDecision
from marinerx_tradeify.payout_engine import calculate_flex_payout
from marinerx_tradeify.risk_engine import gate_trade


def test_eval_consistency_blocks_oversized_day():
    status = evaluate_select_150k_eval(total_profit=9000, largest_winning_day=5000)
    assert status.pass_eligible is False
    assert status.remaining_profit_to_consistency == 3500


def test_eval_passes_clean_three_day_distribution():
    status = evaluate_select_150k_eval(total_profit=9000, largest_winning_day=3000)
    assert status.pass_eligible is True


def test_flex_max_payout_zone():
    days = [DayResult(str(i), 500) for i in range(5)]
    status = calculate_flex_payout(balance=160000, day_results=days)
    assert status.eligible_by_days is True
    assert status.gross_payout_available == 5000
    assert status.trader_net_payout == 4500


def test_flex_not_safe_at_bare_minimum():
    days = [DayResult(str(i), 250) for i in range(5)]
    status = calculate_flex_payout(balance=151250, day_results=days)
    assert status.eligible_by_days is True
    assert status.safe_to_request_under_marinerx_policy is False


def test_risk_gate_reduces_or_blocks_size():
    snapshot = AccountSnapshot(
        phase=AccountPhase.FUNDED_FLEX,
        balance=154000,
        eod_drawdown_floor=150100,
        realized_day_pnl=0,
    )
    signal = SignalIntent(
        symbol="MNQ",
        direction="LONG",
        setup_name="TEST",
        entry_price=20000,
        stop_price=19950,
        target_price=20100,
        contract_type="micro",
        requested_contracts=10,
    )
    result = gate_trade(snapshot, signal)
    assert result.decision in {TradeDecision.REDUCE_SIZE, TradeDecision.ALLOW}
    assert result.projected_risk_dollars <= 250
