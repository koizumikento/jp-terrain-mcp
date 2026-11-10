# 国土地理院の標高

## MCPツール

| ツール | 用途 |
| --- | --- |
| `get_elevation` | 緯度・経度から標高と測量データの種類を取得 |
| `get_elevations` | 指定した1〜10地点の標高と測量データの種類を入力順に取得 |

`get_elevations` は `points` に `latitude` と `longitude` の組を受け取ります。国土地理院には地点ごとに順番に1回ずつ問い合わせます。取得できた標高が2件以上ある場合、`elevation_range_m` に最高値と最低値の差を返します。それ以外は `null` です。


## データの出典と利用条件

標高データのない地点は `elevation_m` と `measurement_source` が `null` になります。国土地理院の試験公開APIを利用します。アクセス頻度を抑えてください。[公式仕様と使用上の注意](https://maps.gsi.go.jp/development/elevation_s.html)

MIT Licenseはこのリポジトリのコードに適用します。
