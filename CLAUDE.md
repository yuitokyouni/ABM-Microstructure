# CLAUDE.md — ABM-Microstructure / 標準事実のみ
<!-- このリポの「動かない事実」だけ。手順は skill、強制は hook、隔離は subagent。lint規則・コードスニペットは書かない。 -->

## What this is
市場微細構造の ABM。能力非対称下で「連続マッチング vs batch auction」が速度ベース抽出(実験A)と学習ベース collusion(実験B)に与える効果を測り、latency-fairness と collusion-resistance のトレードオフを検証する研究リポ。設計一次ソースは `docs/research-design.md`。

## Stack / entrypoints
- 言語/環境: Python 3.13、依存は `uv`（`pip` も可）。Node なし。
- 主要エントリ: `<path/to/main>`（まだ未作成。file:line で指す。スニペットは貼らない）
- 主要パッケージ/モジュール: `<package_name>`（未作成）
<!-- TODO(Yuito): 実装が入ったらここを file:line で埋める。 -->

## Conventions
- spec → plan → tasks → implement の順（Spec Kit 導入後は `/speckit.*`）。spec に無いものを勝手に作らない。
- 図は LLM に描かせず `scripts/generate_diagrams.sh` で決定論的に抽出する。
<!-- このリポ固有の規約だけ追記。一般論は書かない。 -->

## Where the truth lives
- spec: `specs/` および `.specify/memory/constitution.md`（Spec Kit 導入後）
- 用語: `ontology.md`
- 構造図: `docs/architecture.md`（commit ごとに自動再生成）
- 決定: `docs/adr/`
- 人間向け運用マニュアル: `obsidian_ABM_microstructure/00 claude engineering playbook.md.md`

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
