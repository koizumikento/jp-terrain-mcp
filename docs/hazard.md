# J-SHISの地震ハザード

## ツール

いずれも緯度・経度（WGS84）を指定します。

| 調べたいこと | ツール | 選べる条件 |
| --- | --- | --- |
| 今後30年間に、ある震度以上の揺れに見舞われる確率 | `get_earthquake_hazard` | `minimum_jma_intensity` に `5-lower`（5弱）、`5-upper`（5強）、`6-lower`（6弱、既定）、`6-upper`（6強） |
| 指定した超過確率に対応する計測震度 | `get_hazard_intensity` | `period_years` は30年（既定）または50年。`exceedance_probability_percent` は30年なら3%・6%（既定は3%）、50年なら2%・5%・10%・39%（既定は5%） |
| 工学的基盤から地表までの最大速度増幅率、地形の区分、平均S波速度 | `get_surface_ground_amplification` | 表層地盤モデルV4 |

例えば、東京駅付近の今後30年間の震度5強以上の確率を調べるには、`get_earthquake_hazard` に次を渡します。

```json
{
  "latitude": 35.6812,
  "longitude": 139.7671,
  "minimum_jma_intensity": "5-upper"
}
```

確率と計測震度の照会には、J-SHISの2024年版（平均ケース・全地震）を使います。約250m四方の区画ごとの長期評価です。結果には評価の版と出典も含まれます。


## 出典と利用条件

コードはMITライセンスです。地震ハザードと表層地盤のデータは、ツールの実行時に防災科研のJ-SHISから取得します。取得したデータにはJ-SHISの利用規約が適用されます。

- 表層地盤データを資料などに転載・引用する場合は、「表層地盤データ記述ファイル規約」に記載された参考文献を引用してください。
- 地震動予測地図データをそのまま第三者に配布することは、ファイル形式だけを変えた場合も禁止されています。加工した成果物を販売する場合は、防災科研にお問い合わせください。

[J-SHIS利用規約](https://www.j-shis.bosai.go.jp/agreement) · [データと参考文献の案内](https://www.j-shis.bosai.go.jp/download) · [地震ハザードAPI](https://www.j-shis.bosai.go.jp/api-pshm-meshinfo) · [表層地盤API](https://www.j-shis.bosai.go.jp/api-sstruct-meshinfo)
