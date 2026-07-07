# Deployment Checklist

## Phase 1 — Code Integration

- [ ] Copy `src/marinerx_tradeify` into backend source tree.
- [ ] Include router in FastAPI app.
- [ ] Add tests to CI.
- [ ] Add YAML rules file to config loader.
- [ ] Add environment flags.

## Phase 2 — UI Wiring

- [ ] Add Risk Command widget.
- [ ] Add Trade-or-No-Trade gate widget.
- [ ] Add Evaluation Tracker.
- [ ] Add Funded Payout Tracker.
- [ ] Add Settings page rule editor.

## Phase 3 — Safety

- [ ] Confirm all execution paths call `risk_gate` first.
- [ ] Confirm live order routing is disabled by default.
- [ ] Confirm kill switch blocks new orders.
- [ ] Confirm flatten action is simulated unless live execution explicitly enabled.
- [ ] Confirm unknown symbols are blocked.

## Phase 4 — Validation

- [ ] Unit tests pass.
- [ ] Replay test 20 trading days.
- [ ] Confirm max drawdown math.
- [ ] Confirm consistency math.
- [ ] Confirm payout math.
- [ ] Confirm Tradeify current rules manually before funded use.

## Phase 5 — Operations

- [ ] Daily pre-market rule snapshot.
- [ ] Daily post-market risk report.
- [ ] Payout-cycle report every funded winning day.
- [ ] Manual review before every payout request.
