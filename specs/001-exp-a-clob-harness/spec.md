# Feature Specification: 実験A — CLOB 抽出検証 harness

**Feature Branch**: `001-exp-a-clob-harness`（main 上で作業、speckit は .specify/feature.json で追跡）

**Created**: 2026-06-02

**Status**: Draft

**Input**: マイルストーン1 / 実験A。市場微細構造 simulator を解析的真値に対して検証する harness。詳細は `docs/research-design.md` §2/§4/§6、`.specify/memory/constitution.md`、`docs/research-design-review.md`（A1/A2/C4 結び目）。

## Fixed Invariants *(constitution-locked — 冒頭で固定、本 spec 内で変更不可)*

- **市場オブジェクト = CLOB / quoting-MM**。baseline は **inventory-free**（competitive spread を Glosten-Milgrom break-even で定義した結果、market object が quoting-dealer 側に確定。inventory 拡張は実験B＝下流）。AMM/LVR は同じ摩擦の別 venue type の並行/後回し検証アンカーであり、本 harness の spine ではない。
- **非学習のみ**。RL/学習は本 feature に一切含まない。
- **検証先行（原則I）**：解析アンカーに事前設定の許容誤差内で一致するまで、実験B（学習・collusion）に進まない。本 harness の存在意義は「真値の無いBを信じる license」を作ること。
- **knot（A1+C4+C5）**：逆選択源 = arbitrageur（noise trader ではない）。したがって competitive spread = arbitrageur 逆選択への GM break-even であり、これが (i) markup の分母 と (ii) 検証アンカー を**同時に**決める。設計マップ（B）は将来 B 世界で測る——A はその検証アンカーに徹し、findings を出さない。

## User Scenarios & Testing *(mandatory)*

### User Story 1 — 解析アンカーに対する simulator 検証 (Priority: P1)

研究者として、連続マッチング CLOB 上で「ルールベース quoting MM ＋ 反応的 arbitrageur ＋ noise trader」を外生 GBM 価格の下で走らせ、測定された competitive spread と抽出量が、**任意のパラメータ**において Glosten-Milgrom break-even spread・Budish sniping レントの閉形式と**事前設定の許容誤差内で一致**することを確認したい。

**Why this priority**: これが MVP。一致しなければ実験Bを信じる根拠（license）が存在せず、A→B の投資が成立しない。harness の唯一の存在意義がこの検証。

**Independent Test**: 閉形式値が既知のパラメータ点を選び、sim を走らせ、`|sim − closed-form| ≤ tolerance` を assert。単独で完結し、価値（B の license）を出す。

**Acceptance Scenarios**:

1. **Given** 既知パラメータ (σ, fee, arbitrageur 反応規則) と連続 CLOB、**When** sim を十分長く走らせ competitive spread を測る、**Then** 測定値が GM break-even の閉形式と許容誤差内で一致する。
2. **Given** 既知 σ と連続 CLOB、**When** arbitrageur による stale-quote picking-off の抽出量を累積測定する、**Then** Budish sniping レントの閉形式と許容誤差内で一致する。
3. **Given** 同一 seed、**When** 同一設定を再実行する、**Then** 結果は完全再現する（決定論）。

---

### User Story 2 — 連続 vs batch の抽出量定量比較 (Priority: P2)

研究者として、マッチング機構を N 期 uniform-price batch auction に切り替え、速度ベース抽出が連続マッチングに比して**減少**すること（および実効スプレッド・MM 純 PnL の変化）を、理論の定性予測どおりに定量化したい。

**Why this priority**: A の第二の正当な産物（検証に次ぐ「定量化」）。発見ではないが、B の設計レバーが A 世界で期待どおり振る舞うことを確認する。

**Independent Test**: 同一パラメータで連続 / batch を走らせ抽出量を比較。`extraction(batch) < extraction(continuous)` かつ方向が理論と整合、を assert。

**Acceptance Scenarios**:

1. **Given** 同一 (σ, fee) と arbitrageur、**When** 連続と N期 batch でそれぞれ抽出量を測る、**Then** batch の抽出量が連続より小さい。
2. **Given** σ を sweep、**When** 各 σ で連続/batch を比較、**Then** 抽出量の差は σ とともに単調に増える（速度ベース抽出は volatility 駆動）。
3. **Given** batch interval N=1、**When** 連続と比較、**Then** 抽出量はほぼ一致する（N=1 batch ≈ 連続の sanity check）。

---

### User Story 3 — 流動性供給の存続（インセンティブ検査） (Priority: P3)

研究者として、与えられた fee の下で MM 純 PnL（fees − 抽出）が正に保たれ、流動性供給が成立し続けるか（＝設計が LP インセンティブを殺さないか）を確認したい。

**Why this priority**: 「batch が LP インセンティブを殺さないか」の問いに答える補助測度。検証・定量化の後段。

**Independent Test**: fee を sweep し、各機構で MM 純 PnL の符号を測る。

**Acceptance Scenarios**:

1. **Given** 妥当な fee 水準、**When** 連続/batch で MM 純 PnL を測る、**Then** fees − 抽出 が正に保たれる領域が存在する。
2. **Given** fee=0、**When** 抽出が正、**Then** MM 純 PnL は負（fee 無しでは picking-off に晒され続ける、の sanity check）。

---

### Edge Cases

- σ → 0：抽出量はゼロに収束する（価格が動かなければ stale quote の picking-off が起きない）。
- batch 内で true price がジャンプ：同一 batch 内の clearing 価格と逆選択の扱いが定義どおりか。
- 同一 batch 内に複数注文が同時到着：uniform price が単一に決まり、約定割当が決定論的か。
- 複数 arbitrageur が競合：抽出のレース。1体 baseline からの逸脱を測れるか。
- 空板 / 片側のみの板：clearing が破綻せず安全に no-trade になるか。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: harness MUST 外生 GBM の true/fair price を生成し、その価格が**エージェントの取引に影響されない**こと（drift μ, volatility σ、任意で jump 強度 λ）。
- **FR-002**: harness MUST 3種のエージェントを提供する：(a) ルールベース quoting MM（戦略なし・**inventory-free baseline**）、(b) 反応的 arbitrageur ≥1（true price と市場価格の乖離を規則の許す範囲で突く・**学習なし**）、(c) noise/liquidity trader（外生到着・無方向 or 弱需要）。
- **FR-003**: arbitrageur MUST true price 変動時に MM の stale quote を、機構の規則が許す範囲で picking-off する（＝逆選択源は arbitrageur）。
- **FR-004**: harness MUST 連続マッチング（価格優先・時間優先 CLOB）を baseline 機構として提供する。
- **FR-005**: harness MUST N 期 uniform-price batch auction を比較機構として提供する（batch 内全約定が単一 clearing 価格、N をパラメータ化）。
- **FR-006**: harness MUST 抽出量を「MM→arbitrageur の富移転＝arbitrageur の MM 犠牲 PnL の累積」として測定する。
- **FR-007**: harness MUST noise trader の実効スプレッド（(約定価格 − mid) 符号付き）を測定する。
- **FR-008**: harness MUST MM 純 PnL（fees − 抽出）を測定する。fee 水準は明示パラメータ（固定・sweep 可能）。
- **FR-009**: harness MUST competitive spread を **arbitrageur 逆選択への Glosten-Milgrom break-even** として算出する（markup 分母と検証アンカーを兼ねる）。
- **FR-010**: harness MUST 任意のパラメータ点で、上記測定を該当する閉形式アンカー（GM break-even spread / Budish sniping レント）と照合し、**事前設定の許容誤差**内の一致/不一致を判定・報告する。
- **FR-011**: harness MUST seed を与えれば完全再現すること、および複数 seed の集計をサポートすること。
- **FR-012**: harness MUST RL/学習・collusion 測定・inventory 状態・compute grid を**含まない**（本 feature のスコープ外、FR で明示的に除外）。

### Key Entities

- **TruePrice**: 外生 GBM 過程。drift μ, volatility σ, 任意 jump λ。取引から独立。
- **Quote / Order**: MM の気配、arbitrageur/noise の注文。価格・サイド・サイズ・到着時刻。
- **Fill / Trade**: 約定。価格・数量・対向当事者（逆選択帰属の判定に使う）。
- **Agent**: MM（inventory-free・規則）/ Arbitrageur（反応・学習なし）/ Noise（無方向）。
- **MarketMechanism**: Continuous（価格時間優先）/ Batch（N 期 uniform-price）。
- **Metric**: Extraction（累積富移転）/ EffectiveSpread / MM net PnL / CompetitiveSpread(GM)。
- **VerificationAnchor**: GM break-even / Budish sniping rent / （並行）AMM-LVR。許容誤差と判定を保持。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 連続 CLOB の measured competitive spread が GM break-even 閉形式と、**≥8 個のパラメータ点**で事前設定許容誤差内に一致する。
- **SC-002**: measured sniping 抽出量が Budish 閉形式と、σ sweep 全域で許容誤差内に一致する。
- **SC-003**: N 期 batch の抽出量が、同一パラメータの連続マッチングに比して測定可能かつ理論整合的に減少し、その差が σ とともに単調増加する。
- **SC-004**: 任意の seed で結果が完全再現する（同一入力→同一出力）。
- **SC-005（B への gate）**: SC-001〜SC-002 が全て pass した時点で、「実験B（真値なし）を信じる license が成立」と判定・記録する。pass しなければ B に進まない。

## Assumptions

- **許容誤差のデフォルト**：相対誤差 ≤ 5% もしくは Monte Carlo 標準誤差の 2 倍以内のいずれか緩い方。アンカーごとに事前設定し spec/plan で固定（合理的デフォルトのため NEEDS CLARIFICATION にはしない）。
- **arbitrageur 数**：baseline は 1 体。複数体は edge case/感度として扱う（B 本番の sweep ではない）。
- **fee 水準**：明示パラメータ。検証は fee=0 を含む複数水準で行う。
- **AMM/LVR アンカー**：spine ではなく別 venue type の**並行/後回し**検証。本 feature の SC には含めない（含めると market object が二重化し knot に反する）。
- **検証は内部整合で十分**：解析モデル相手に任意パラメータで正しさを示せばよく、**実在 venue/銘柄へのアンカーは不要**（findings の外部妥当性は実験B＝下流の関心）。
- **C6（文献調査）は並行**：本 harness の実装と独立に進む B の novelty 検査であり、A の spec を変更しない。

## Out of Scope *(本 feature では扱わない — 実験B/下流)*

学習/RL エージェント、tacit collusion の測定、competitive benchmark の myopic-Nash 一般化（A では GM break-even で確定）、inventory 拡張（C3-B）、compute 予算/grid 設計（B1）、外部妥当性アンカー＝実在銘柄（④）、AMM/LVR を spine にすること、novelty 主張（C6）。
