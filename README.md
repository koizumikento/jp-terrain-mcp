# jp-terrain-mcp

緯度・経度から、標高、地質、地震ハザードを調べるMCPサーバーです。MCP、CLI、Pythonライブラリから同じ機能を使えます。

[準備](#準備) · [MCP登録](#mcpクライアントに登録する) · [CLI](#cliで使う) · [Python](#pythonで使う) · [移行手順](docs/migration.md)

## 準備

Python 3.12以上、[uv](https://docs.astral.sh/uv/)、Gitが必要です。

```sh
git clone https://github.com/koizumikento/jp-terrain-mcp.git
cd jp-terrain-mcp
uv sync --locked
```

APIキーは不要です。

## MCPクライアントに登録する

設定例の `/absolute/path/to/jp-terrain-mcp` をクローン先の絶対パスに置き換えます。Windowsでは `C:/projects/jp-terrain-mcp` のように書けます。

### Codex

```sh
codex mcp add jp-terrain-mcp -- uv --directory "/absolute/path/to/jp-terrain-mcp" run --locked jp-terrain-mcp
codex mcp list
```

新しいセッションで `/mcp` を開いて接続状態を確認します。

### Claude Desktop / Cursor

Claude DesktopはOSに応じて次のファイルに設定します。

- Windowsは `%APPDATA%/Claude/claude_desktop_config.json`
- macOSは `~/Library/Application Support/Claude/claude_desktop_config.json`

Cursorはプロジェクト内の `.cursor/mcp.json` を使います。`mcpServers` に次の項目を追加し、クライアントを再起動してください。

```json
{
  "mcpServers": {
    "jp-terrain-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/jp-terrain-mcp",
        "run",
        "--locked",
        "jp-terrain-mcp"
      ]
    }
  }
}
```

`uv` が見つからない場合は、`command` に実行ファイルの絶対パスを指定してください。

## ツール

データごとの入力条件、結果、出典と利用条件は、表のリンク先に記載しています。

| ツール | データと操作の説明 |
| --- | --- |
| `get_elevation` | [国土地理院の標高](docs/elevation.md) |
| `get_elevations` | [国土地理院の標高](docs/elevation.md) |
| `get_geology` | [産総研の地質図](docs/geology.md) |
| `get_area_geology` | [産総研の地質図](docs/geology.md) |
| `get_earthquake_hazard` | [J-SHISの地震ハザード](docs/hazard.md) |
| `get_hazard_intensity` | [J-SHISの地震ハザード](docs/hazard.md) |
| `get_surface_ground_amplification` | [J-SHISの地震ハザード](docs/hazard.md) |

## CLIで使う

クローン先で実行します。取得結果はUTF-8のJSONとして標準出力に書き出します。

```sh
uv run jp-terrain-mcp elevation get-elevation --latitude 36.103543 --longitude 140.08531
uv run jp-terrain-mcp geology get-geology --latitude 39.7 --longitude 141.15
uv run jp-terrain-mcp hazard get-earthquake-hazard --latitude 35.6812 --longitude 139.7671
```

引数の説明は、各サブコマンドに `--help` を付けて確認できます。

## Pythonで使う

自分のPythonプロジェクトの依存関係に追加します。

```sh
uv add "git+https://github.com/koizumikento/jp-terrain-mcp.git@main"
```

次のコードを `example.py` に保存し、`uv run python example.py` で実行します。

```python
import asyncio

from jp_terrain_mcp import get_elevation

result = asyncio.run(get_elevation(latitude=36.103543, longitude=140.08531))
print(result)
```

ツールと同じ名前の非同期関数を利用できます。すでにイベントループがある場合は、直接 `await` してください。

## 出典と利用条件

コードはMITライセンスです。データは実行時に各提供元から取得します。取得データには、データ別の説明に記載した提供元の利用条件が適用されます。

## 開発

```sh
uv sync --locked
uv run ruff check .
uv run ty check
uv run pytest
uv build
```
