"""SC-001/005: sim を解析アンカーに照合。

判定（D6）: tight な統計 consistency（複数 seed の SE）＋ 形/スケーリング再現。
flat な「緩い方 5%」は使わない。小さい abs floor のみ補助に置く。
"""
from dataclasses import replace

import numpy as np
import pytest

from microstructure import SimConfig, measure_competitive_spread, run
from microstructure import anchors

# coverage: alpha・lambda(=vol proxy)・J の関連レンジ＋stress（高 lambda・大 J）
GM_PARAMS = [
    dict(alpha=0.2, lambda_jump=5.0, jump_size=1.0),
    dict(alpha=0.3, lambda_jump=5.0, jump_size=1.0),
    dict(alpha=0.5, lambda_jump=5.0, jump_size=1.0),
    dict(alpha=0.2, lambda_jump=10.0, jump_size=1.0),
    dict(alpha=0.3, lambda_jump=8.0, jump_size=2.0),
    dict(alpha=0.5, lambda_jump=10.0, jump_size=1.0),
    dict(alpha=0.1, lambda_jump=5.0, jump_size=1.0),
    dict(alpha=0.4, lambda_jump=15.0, jump_size=1.5),  # stress
]


@pytest.mark.parametrize("p", GM_PARAMS)
def test_gm_break_even_matches(p):
    base = SimConfig(n_periods=120000, seed=0, dt=1e-2, noise_rate=1.0,
                     mechanism="continuous", **p)
    anchor = anchors.gm_break_even(p["lambda_jump"], p["jump_size"],
                                   p["alpha"], base.noise_rate)
    hbe = np.array([measure_competitive_spread(replace(base, seed=s))
                    for s in range(5)])
    mean, se = hbe.mean(), hbe.std(ddof=1) / np.sqrt(len(hbe))
    tol = max(base.se_mult * se, 0.03 * anchor)  # tight SE 主、わずかな floor
    assert abs(mean - anchor) <= tol, f"sim {mean:.4f} vs anchor {anchor:.4f} (tol {tol:.4f})"


def test_gm_dt_stability():
    """dt→0 でアンカーは不変（dt が cancel する連続時間極限）。粗/細 dt で h* が安定。"""
    p = dict(alpha=0.3, lambda_jump=5.0, jump_size=1.0)
    anchor = anchors.gm_break_even(p["lambda_jump"], p["jump_size"], p["alpha"], 1.0)
    coarse = measure_competitive_spread(
        SimConfig(n_periods=120000, seed=0, dt=1e-2, noise_rate=1.0, **p))
    fine = measure_competitive_spread(
        SimConfig(n_periods=240000, seed=0, dt=5e-3, noise_rate=1.0, **p))
    assert abs(coarse - anchor) < 0.1 * anchor
    assert abs(fine - anchor) < 0.1 * anchor


@pytest.mark.parametrize("J", [1.0, 2.0, 3.0])
def test_informed_impact_equals_jump(J):
    """SC-005 impact 層: informed 取引の price impact = J（sigma=0 では厳密）。"""
    cfg = SimConfig(n_periods=80000, seed=3, dt=1e-2, alpha=0.4, lambda_jump=8.0,
                    jump_size=J, half_spread=0.1 * J, noise_rate=1.0, sigma=0.0)
    m = run(cfg).metrics
    assert m.informed_impact == pytest.approx(J, rel=1e-9)
    assert anchors.kyle_lambda(J) == pytest.approx(J)


def test_extraction_nonnegative_and_accounting():
    cfg = SimConfig(n_periods=80000, seed=1, dt=1e-2, alpha=0.3, lambda_jump=8.0,
                    jump_size=1.0, half_spread=0.1, noise_rate=1.0)
    m = run(cfg).metrics
    assert m.extraction >= 0
    assert m.mm_trading_pnl == pytest.approx(m.noise_pnl - m.extraction)
