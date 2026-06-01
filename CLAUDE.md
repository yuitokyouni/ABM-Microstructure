# CLAUDE.md — ABM-Microstructure / 標準事実のみ
<!-- このリポの「動かない事実」だけ。手順は skill、強制は hook、隔離は subagent。lint規則・コードスニペットは書かない。 -->

## What this is
市場微細構造の ABM。能力非対称下で「連続マッチング vs batch auction」が速度ベース抽出(実験A)と学習ベース collusion(実験B)に与える効果を測り、latency-fairness と collusion-resistance のトレードオフを検証する研究リポ。設計一次ソースは `docs/research-design.md`。

## Stack / entrypoints
- 言語/環境: Python 3.13、依存は `uv`（`pip` も可）。numpy + pytest。ABM フレームワーク不使用。Node なし。
- 計画パッケージ: `src/microstructure`（M1 plan で確定、コードは未実装）。エントリ `microstructure.run(SimConfig) -> RunResult`。
- 構造図の対象: `ABM_PKG=src/microstructure`。
<!-- 実装が入ったら主要モジュールを file:line で指す。スニペットは貼らない。 -->

## Conventions
- spec → plan → tasks → implement の順（`/speckit-*`、ハイフン）。spec に無いものを勝手に作らない。
- 図は LLM に描かせず `scripts/generate_diagrams.sh` で決定論的に抽出する。
<!-- このリポ固有の規約だけ追記。一般論は書かない。 -->

## Where the truth lives
- spec: `specs/` および `.specify/memory/constitution.md`（Spec Kit 導入後）
- 用語: `ontology.md`
- 構造図: `docs/architecture.md`（commit ごとに自動再生成）
- 決定: `docs/adr/`
- 人間向け運用マニュアル: `obsidian_ABM_microstructure/00 claude engineering playbook.md.md`

<!-- SPECKIT START -->
現在アクティブな feature: 実験A harness。plan = `specs/001-exp-a-clob-harness/plan.md`
（spec.md / research.md / data-model.md / contracts/sim-interface.md / quickstart.md）。
technologies・project structure・コマンドはここを読む。
<!-- SPECKIT END -->
