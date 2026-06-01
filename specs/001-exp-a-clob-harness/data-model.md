# Phase 1 Data Model — 実験A

spec の Key Entities を具体 dataclass に落とす。全て `src/microstructure/` 内。型は実装時に確定（ここは形と不変条件）。

## SimConfig (`config.py`)
不変の run パラメータ。frozen dataclass。
- `n_periods: int` — sim 長
- `seed: int` — 単一 RNG seed（D7）
- price: `mu: float`(drift), `sigma: float`(vol, 主要 sweep), `p_jump: float`, `jump_size: float`(J), `use_diffusion: bool`(GBM 拡張 flag, baseline=False)
- mechanism: `mechanism: Literal["continuous","batch"]`, `batch_interval: int`(N; continuous では無視)
- flow: `alpha: float`（taker が arbitrageur である確率＝informed fraction）, `noise_rate: float`
- fee: `fee: float`（taker fee 正 / maker rebate 負）
- `tolerance_rel: float = 0.05`, `tolerance_se_mult: float = 2.0`（D6）
- 不変条件: `0<=alpha<=1`, `0<=p_jump<=1`, `batch_interval>=1`, `sigma>=0`。

## TruePrice (`price.py`)
- `value(t) -> float`：外生 GBM(+jump)。**取引に依存しない**（FR-001）。RNG は engine 注入。
- 状態: 現在値 `v`、直近ジャンプ有無（staleness 判定に使う）。

## Order / Quote (`book.py`)
- `Order(side: Side, price: float, size: float, agent_id: str, t: int, seq: int)`
- `Side = Enum(BUY, SELL)`。`seq` は時間優先のための単調 ID。

## OrderBook (`book.py`)
- 価格優先・時間優先。`add(order)`, `best_bid()`, `best_ask()`, `mid()`, `match_continuous() -> list[Fill]`, `clear_uniform(orders) -> (clearing_price, list[Fill])`。
- batch clearing は uniform price（supply/demand 交点、marginal quote が全約定に効く＝demand-reduction の素地）。

## Fill / Trade (`book.py`)
- `Fill(price, size, buyer_id, seller_id, t)`。逆選択帰属（arbitrageur が aggressor か）を判定可能に。

## Agents (`agents.py`)
- `MarketMaker`：inventory-free。`quote(mid, t) -> (bid_order, ask_order)`。規則ベース（戦略・学習なし）。半スプレッドは config 由来 or 簡易規則（competitive 近傍を出すが、それ自体は検証対象＝外から測る）。
- `Arbitrageur`：`react(true_price, book, t) -> list[Order]`。stale quote が利益的なら即 picking-off（D3）。**学習なし**。`>=1` 体。
- `NoiseTrader`：`arrive(rng, book, t) -> Optional[Order]`。無方向（50/50）or 弱需要。
- 不変条件: どの agent も `V` の未来を知らない（arbitrageur は現在 `V` のみ＝informed の定義）。

## MarketMechanism (`mechanisms.py`)
protocol。`step(book, orders, t) -> list[Fill]`。
- `ContinuousMatching`：到着順に price-time priority で即時マッチ。
- `BatchAuction(N)`：N 期分を集約し uniform price で一括 clearing。
- 差し替えで US2（連続 vs batch）が同一コードパスで比較可能。

## Metrics (`metrics.py`)
run 全体を集計。
- `extraction: float`（arbitrageur 累積 PnL = MM 犠牲、D8。ゼロサム assert）
- `effective_spread: float`（noise traders、D8）
- `mm_net_pnl: float`（fees − extraction）
- `competitive_spread: float`（sim から測った実効 half-spread。GM アンカーと比較する量）
- `realized_spread`, per-seed の分散（SE 推定用）

## Anchors (`anchors.py`) — sim と独立実装
- `gm_break_even(p_jump, jump_size, alpha, ...) -> float`（competitive half-spread の閉形式, D4）
- `budish_sniping_rent(sigma, p_jump, jump_size, batch_interval, ...) -> float`（抽出量の閉形式, D5）
- **engine/metrics を import しない**（共有バグ排除）。手計算1点を test で pin。

## RunResult (`engine.py`)
- `RunResult(config: SimConfig, metrics: Metrics, n_trades: int, runtime_sec: float)`。
- `runtime_sec` は B1（compute 予算）の入力。
