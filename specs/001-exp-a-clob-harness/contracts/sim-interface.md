# Contract — sim 公開インターフェース（実験A）

内部 research library のため「contract」= 公開 API 面と不変条件。実装はこの形に従う。

## 1. エントリポイント
```
microstructure.run(config: SimConfig) -> RunResult
```
- 純関数的: 同一 `config`（同一 seed 含む）→ 同一 `RunResult`（SC-004）。
- 副作用なし（I/O は呼び出し側＝scripts/tests）。

## 2. SimConfig（入力スキーマ）
`config.py` の frozen dataclass。フィールドは data-model.md 参照。
- 必須: `n_periods, seed, sigma, p_jump, jump_size, alpha, mechanism`。
- `mechanism="batch"` の時のみ `batch_interval` が有効。
- バリデーション: 範囲外は `ValueError`。

## 3. RunResult（出力スキーマ）
- `metrics.extraction`, `.effective_spread`, `.mm_net_pnl`, `.competitive_spread`
- `n_trades: int`, `runtime_sec: float`
- ゼロサム不変: `metrics` 内で arbitrageur 利得 == MM 逆選択損（許容丸め内）。

## 4. MarketMechanism protocol
```
class MarketMechanism(Protocol):
    def step(self, book: OrderBook, orders: list[Order], t: int) -> list[Fill]: ...
```
- 実装: `ContinuousMatching`, `BatchAuction(interval: int)`。
- `BatchAuction` は clearing 価格を単一に決め、全約定に同一価格を適用（uniform-price）。

## 5. anchors API（解析的真値・sim と独立）
```
gm_break_even(p_jump: float, jump_size: float, alpha: float) -> float        # competitive half-spread
budish_sniping_rent(sigma: float, p_jump: float, jump_size: float,
                    batch_interval: int = 1) -> float                        # per-run 期待抽出量
```
- これらは `engine`/`metrics`/`agents` を import してはならない（共有バグ排除＝検証の独立性）。
- 正確な定数は実装で導出し、手計算1点を `test_anchors_match.py` で pin。

## 6. 検証コントラクト（テストが満たすべき判定）
- `assert rel_err(sim.competitive_spread, gm_break_even(...)) <= tol` を ≥8 パラメータ点で（SC-001）。
- `assert rel_err(sim.extraction, budish_sniping_rent(...)) <= tol` を σ sweep 全域で（SC-002）。
- `assert extraction(batch) < extraction(continuous)` かつ差が σ で単調（SC-003）。
- `assert run(cfg) == run(cfg)`（SC-004）。
- `tol = max(tolerance_rel * |anchor|, tolerance_se_mult * SE)`（D6）。

## 7. CLI / sweep コントラクト
```
python scripts/run_sweep.py --sigma 0.1,0.2,0.4 --N 1,5,20 --fee 0,0.0005 --seeds 8 --out results.csv
```
- 各セルの `runtime_sec` を出力（B1 入力）。stdout は人間可読サマリ、`--out` で機械可読。
