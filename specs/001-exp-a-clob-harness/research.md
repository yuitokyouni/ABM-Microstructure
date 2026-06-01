# Phase 0 Research — 実験A harness の技術判断

各項目 Decision / Rationale / Alternatives。非自明な判断は `docs/adr/` にも1枚残す候補。

## D1. 言語 = Python 3.13
- **Decision**: Python。
- **Rationale**: 環境既存、numpy で GBM/RNG/閉形式が簡潔、pytest で検証をそのまま成果物化。research-design §6 が「数百行規模」と言う通り、速度より監査性・可読性が要件。
- **Alternatives**: Julia/Rust（速いが、A の規模では over-engineering。B で grid が重くなったら hot path だけ移植を検討＝下流）。

## D2. ABM フレームワーク不使用（ADR 候補）
- **Decision**: Mesa / ABIDES 等を使わず、purpose-built な小エンジンを書く。
- **Rationale**: 本 feature の唯一の価値は「sim 出力が閉形式と一致する」ことの監査可能な証明（原則I・auditability）。フレームワークは scheduler/agent 抽象を不透明に挟み、閉形式と sim の差分の原因切り分けを難しくする。数百行の自前ループの方が「どの行がアンカーと対応するか」を追える。
- **Alternatives**: Mesa（教育向け、連続/uniform-price batch の clearing を厳密に書くのに不向き）、ABIDES（重い、LOB は本格的だがセットアップ/監査コストが A に過剰）。→ 却下。

## D3. arbitrageur の latency / sniping モデル（速度非対称の表現）
- **Decision**: BCS 型の **1 期 staleness**。各 period: (1) true price 更新 → (2) **arbitrageur（ゼロ latency）が更新後価格を観測し、MM の更新前 stale quote が利益的なら即 picking-off** → (3) MM は次 period の頭で気配を更新。noise trader は到着して mid 周りで約定。
- **Rationale**: これが「速い主体が stale quote を抜く」を最小に表現し、Budish の sniping 構造と GM の逆選択源を同一主体（arbitrageur）に統一する（knot）。MM の速度劣位＝quote 更新が 1 期遅れる、で表現。
- **Alternatives**: 連続時間ポアソン到着＋明示 latency δ（より現実的だが閉形式照合が煩雑）。→ A では離散 1 期 staleness、連続時間化は B/将来。

## D4. Glosten-Milgrom break-even（competitive spread の解析アンカー）
- **モデル primitives（閉形式が出るよう sim primitive をこれに一致させる）**:
  - fundamental `V`。各 period、確率 `p_jump` で ±`J` のジャンプ（対称）、それ以外は不変（baseline。GBM diffusion 版は拡張）。
  - 各 period に taker 1名到着：確率 `alpha` で arbitrageur（informed＝ジャンプ後 `V` を知り、利益的な側を取る）、確率 `1-alpha` で noise（50/50 で買い/売り、無情報）。
  - MM は mid `m`（`V` の事前期待）周りに half-spread `h` で両側気配（inventory-free＝在庫で歪めない）。
- **break-even 条件**: ゼロ利潤 `E[MM profit | trade] = 0`。informed 買いで MM は `(V-ask)` を失い、noise 買いで `h` を得る。これを解いた `h*` が competitive half-spread。
- **Decision**: `anchors.gm_break_even(p_jump, J, alpha, ...)` が `h*` を**閉形式で**返す。正確な定数は anchors.py で導出し、**手計算した1点を unit test で pin**（plan に定数を書いて誤りを密輸しない）。sim 側 `metrics.competitive_spread` は同じ primitives の sim から測った h で、両者の一致が SC-001。
- **Rationale**: 解析側と sim 側が同一概念・別実装＝共有バグを排除（A2/構造決定）。
- **Alternatives**: 連続 GM（Kyle λ）も別アンカーに使えるが、A の主アンカーは離散 GM。Kyle は将来の追加チェック。

## D5. Budish sniping レント（抽出量の解析アンカー）
- **Decision**: 同一 primitives 上で、連続マッチングの per-period sniping 損 = 「stale quote がジャンプで取り残され picking-off される確率 × 逆選択サイズ」。`anchors.budish_sniping_rent(...)` が閉形式で返す。N 期 batch は N 期分の到着を 1 回の uniform-price clearing に集約し、intra-batch の picking-off 機会を除去 → レントが N とともに減少。
- **検証**: SC-002（σ/p_jump sweep 全域で sim 抽出量 ≈ 閉形式）、SC-003（batch/continuous 比が N・σ で理論整合）。
- **Alternatives**: AMM-LVR（Milionis）は別 venue type のアンカー＝spine 外、並行/後回し（spec Assumptions）。

## D6. 許容誤差
- **Decision**: アンカーごとに事前設定。デフォルト = **相対誤差 ≤ 5% または Monte Carlo 標準誤差の 2 倍以内の緩い方**。`SimConfig.tolerance` で上書き可。MC SE は seed 集計から推定。
- **Rationale**: sim は有限サンプル＝統計誤差を持つ。固定 5% だけだと低分散領域で甘く高分散領域で厳しすぎる。SE ベースを併用。

## D7. 決定論
- **Decision**: 単一 `numpy.random.default_rng(seed)` を engine が保持し、price/agents/arrival の全乱数をそこから引く。`SimConfig.seed`。複数 seed は外側ループ（検証・sweep）で回す。
- **Rationale**: FR-011・SC-004。再現性が監査の前提。

## D8. 抽出量・実効スプレッドの会計定義
- **extraction**: arbitrageur の各約定 PnL = `(true price − 約定価格) × 符号付き数量` の累積（MM 犠牲分）。MM 側に同額の逆符号で計上 → ゼロサム整合を assert（会計の sanity check）。
- **effective spread**: noise trader の約定について `2 × |約定価格 − mid|`（符号付き版も保持）。
- **mm_net_pnl**: `fees 収入 − extraction`。fee は taker fee/maker rebate を `SimConfig.fee` で表現。

## 残 NEEDS CLARIFICATION
- なし（全項目 Decision 済）。GM/Budish の正確な定数は実装フェーズで導出し unit test で pin する設計とした（plan に数値を埋めない）。
