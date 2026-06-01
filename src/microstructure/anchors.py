"""解析アンカー（連続時間極限）。

**重要**: このモジュールは engine/metrics/agents/book を import しない。
sim と独立実装することで「検証の真値」が sim ロジックのバグを共有しないことを構造で担保する
(research D5 / A2)。LVR は無い（CLOB に pool 不在）。
"""
from __future__ import annotations

import math


def gm_break_even(lambda_jump: float, jump_size: float, alpha: float,
                  noise_rate: float) -> float:
    """Glosten-Milgrom 競争（zero-profit）half-spread h*。

    モデル（research D4）: MM は belief m 周りに ±h で両側気配。各ステップ
    確率 lambda*dt で ±J ジャンプ。jump 後、informed(arbitrageur, 確率 alpha)が
    stale quote を picking-off（J>h なら利益 J-h）。noise(強度 noise_rate)は無方向で
    half-spread h を MM に支払う。
    zero-profit: noise_rate * h = alpha * lambda * (J - h)
      => h* = alpha*lambda*J / (noise_rate + alpha*lambda)
    （dt は両辺で cancel ＝連続時間極限。常に h* < J）。
    """
    denom = noise_rate + alpha * lambda_jump
    if denom <= 0:
        return 0.0
    return alpha * lambda_jump * jump_size / denom


def budish_sniping_rent(sigma: float, lambda_jump: float, jump_size: float,
                        alpha: float, noise_rate: float,
                        batch_interval: int = 1) -> float:
    """連続マッチング(N=1)の単位時間あたり期待 sniping 抽出量（連続時間極限）。

    rent = alpha * lambda * (J - h*),  h* = gm_break_even(...)
         = alpha*lambda*J * noise_rate / (noise_rate + alpha*lambda)
    batch_interval N>1 では intra-batch のジャンプが net され picking-off 機会が減るため
    rent は N とともに減少する（厳密な閉形式は与えず、sim で単調性/スケーリングを検証＝SC-003）。
    ここでは N=1 の連続時間値のみを厳密アンカーとして返す（N>1 は近似 1/N を参考値）。
    """
    h_star = gm_break_even(lambda_jump, jump_size, alpha, noise_rate)
    rent_continuous = alpha * lambda_jump * (jump_size - h_star)
    if batch_interval <= 1:
        return rent_continuous
    # 参考: 粗い縮小スケール（厳密検証は sim 側の単調性で行う）
    return rent_continuous / batch_interval


def kyle_lambda(jump_size: float, alpha: float | None = None) -> float:
    """price impact 係数（model-consistent）。

    informed(arbitrageur)の取引後、MM は真値を学習し mid が J だけ動く。
    **informed 取引1回あたりの price impact = J**（jump model では alpha は頻度に効くが
    1取引あたり impact には効かない）。検証はこのスケーリング（∝ J、informed で ~J）を
    sim の `informed_impact` と照合（SC-005, impact 層）。`alpha` は API 互換のため任意。
    """
    return jump_size
