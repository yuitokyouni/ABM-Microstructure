"""T019: 予算 ledger の enforcement・memory 閾値 gate・coarse 構成の静的予算検査・
cell_id 往復・runner CLI スモーク（specs/002 US3）。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from microstructure import anchors
from microstructure.calibrations import (CalibrationIncomplete, get_calibration)
from microstructure.designmap import (BudgetExceeded, BudgetLedger, cell_id,
                                      coarse_grid, parse_cell_id,
                                      robustness_variants, _planned_periods)
from microstructure.learnconfig import LearnConfig
from microstructure.verdict import CollusionVerdict, memory_threshold


def _verdict(certified: bool) -> CollusionVerdict:
    return CollusionVerdict(markup_mean=0.3, markup_se=0.01, markup_significant=certified,
                            ir_pass_frac=1.0 if certified else 0.0,
                            converged_all=True, certified=certified, n_seeds=5)


def test_ledger_enforces_cap_and_logs_refusal(tmp_path):
    path = tmp_path / "budget.json"
    led = BudgetLedger(path, caps={"coarse": 100, "dense": 100, "robustness": 100})
    led.charge("coarse", 60)
    with pytest.raises(BudgetExceeded):
        led.charge("coarse", 60)                    # 60+60 > 100 → 起動拒否
    data = json.loads(path.read_text())
    assert data["spent"]["coarse"] == 60            # 拒否分は計上されない
    assert data["refusals"][0]["requested"] == 60   # 拒否が記録される
    led.refund("coarse", 10)
    led2 = BudgetLedger(path, caps={"coarse": 100, "dense": 100, "robustness": 100})
    assert led2.data["spent"]["coarse"] == 50       # 永続・再読込
    led2.charge("coarse", 50)                       # 返金分で再び通る


def test_memory_threshold_gate():
    assert memory_threshold({0: _verdict(False), 1: _verdict(True),
                             2: _verdict(True)}) == 1
    with pytest.raises(ValueError):
        memory_threshold({0: _verdict(False), 1: _verdict(False)})  # 認定ゼロ=閾値未定義
    with pytest.raises(ValueError):
        memory_threshold({})


def test_coarse_grid_fits_tier_budget():
    """D-B9 静的検査: coarse の予定総期数（t_max 基準・5 seed）が tier 上限以下。"""
    cells = coarse_grid()
    assert len(cells) == 72   # (memory=2, n=3) は tabular 不能で除外（D-B9 実装注記）
    planned = sum(_planned_periods(cfg) * 5 for cfg in cells)
    assert planned <= BudgetLedger.DEFAULT_CAPS["coarse"]
    ids = [cell_id(c) for c in cells]
    assert len(set(ids)) == 72                      # cell id は一意


def test_cell_id_roundtrip():
    for cfg in (LearnConfig(mechanism="batch", batch_interval=20, staleness="revisable",
                            lambda_jump=15.0, jump_size=1.5, fee=0.075, memory=2,
                            n_mm=2, algo="sarsa"),
                LearnConfig()):
        rt = parse_cell_id(cell_id(cfg))
        assert cell_id(rt) == cell_id(cfg)


def test_robustness_variants_cover_d_b9():
    base = LearnConfig()
    variants = robustness_variants(base)
    algos = {cfg.algo for cfg, _ in variants}
    assert "sarsa" in algos                          # 第2アルゴリズム
    assert any(cfg.tie_rule == "rotate" for cfg, _ in variants)
    assert any(s >= 20 for _, s in variants)         # headline 追加 seed


def test_bcs_calibration_eq3_closure():
    """④: BCS eq(3) closure の検算 — 較正 ν の下で GM break-even が観測 half-spread
    0.125pt を厳密再現（換算チェーンの内部整合、calibration.md）。"""
    cfg = get_calibration("bcs-es-spy").to_config()
    hstar = anchors.gm_break_even(cfg.lambda_jump, cfg.jump_size, cfg.alpha,
                                  cfg.noise_rate)
    assert hstar == pytest.approx(0.125, rel=1e-12)
    assert cfg.action_grid[0] < 0.125 < cfg.action_grid[-1]   # 観測 h は grid 内


def test_incomplete_calibration_refuses_to_run():
    """未記入の較正値で走らせない（出典なしの数値を黙って埋めない、原則V）。"""
    with pytest.raises(CalibrationIncomplete):
        get_calibration("twse-call-auction").to_config()


def test_runner_cli_smoke(tmp_path):
    """CLI が縮小スケールで CSV と ledger を出す（quickstart の入口検証）。"""
    out = tmp_path / "map.csv"
    ledger = tmp_path / "budget.json"
    cmd = [sys.executable, "scripts/run_design_map.py", "--tier", "coarse",
           "--limit", "1", "--seeds", "2", "--t-max", "4000",
           "--out", str(out), "--budget-ledger", str(ledger)]
    res = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[1])
    assert res.returncode == 0, res.stderr
    assert out.exists()
    spent = json.loads(ledger.read_text())["spent"]["coarse"]
    assert 0 < spent <= 2 * (4000 + 100 + 400)       # 実消費が記帳されている
