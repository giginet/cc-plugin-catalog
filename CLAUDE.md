# cc-plugin-catalog

このプロジェクトはClaude Code Plugin Marketplaceのインデックスページを生成するためのPython Packageです。

Marketplaceの仕様：https://code.claude.com/docs/ja/plugin-marketplaces
オフィシャルプラグインMarketplace: https://github.com/anthropics/claude-plugins-official

以下のプロダクトを提供します。

オフィシャルプラグインマーケットのリポジトリを参考に構築してください。

## 静的サイトジェネレーター

Plugin Marketplaceのリポジトリから静的なHTMLを生成します

- 一覧ページ（グリッド上に表示）とプラグインごとのパーマリンク
- リポジトリ内の`.claude-plugin/marketplace.json`, `plugins/**/plugin.json`を読み込んでメタデータを表示する。
- pluginsディレクトリのうち、サポートしているツールを表示する
    - Skill, Hooks, MCP, Subagent, Commands, LSP server
    - 提供しているSkillやSubagent, Command名、Hookのイベント名なども表示する
- LICENSE, README.mdが含まれていればそれも表示する（Markdownレンダリング）
- Light Mode / Dark Modeの切り替え

## GitHub Actions Workflow

各Marketplaceリポジトリが簡単に静的ページを作ってGitHub PagesにデプロイできるようなReusable Workflowを提供します。

## CI/CD

- GitHub Actions Workflow
    - pytest
    - ruff
    - ty
