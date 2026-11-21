# R22.2 現在の入口

[今後の命令追加時のデコード配置](DECODE_EXTENSION_RULES.md)。

[R22.2の変更・既知不具合・比較手順](R22_2_ED_DECODE_COMPARISON.md)。命令の機能はR22と同一。GOWIN/実機は未確認。以下は旧版履歴。

# R22ドキュメント

- [R22追加機能・幅・共用・テスト](R22_BLOCK_IO_REPEAT.md)
- [最新の命令実装一覧](EZ80_INSTRUCTION_STATUS_R22.md)
- [残る工程](REMAINING_R22.md)
- [R21.3デコード説明](EZ80_DECODE_IMPLEMENTATION_R21_3.md)
- [R21.3最悪Setup経路](EZ80_WORST_SETUP_PATH_R21_3.md)

以下はR21.3時点の履歴。R22の合成・実機は未確認。

---

# R21.3 資料一覧

## 現在の状態

ユーザー実機でEZ80MEM / EZ80IO2 / EZ80MR4 / RUNALL全項目PASS、SOFARUNからスペースマンボウ起動・PLAYを確認済み。
GOWIN: Logic94%、LUT17208、ALU1877、Register7393。観測用31bit保持が合成後も残る。
最悪Setup−7.654ns、Hold−2.712ns。タイミング未達と、R21〜R21.1のメモリ不具合の原因特定は未解決。

| 資料 | 内容 |
| --- | --- |
| [R19〜R21.3の変更履歴](R19_TO_R21_3_CHANGELOG.md) | 追加命令・互換修正・診断・除外方針、途中で採用しなかった機能 |
| [命令一覧・実装状況](EZ80_INSTRUCTION_STATUS_R21_3.md) | 97ニーモニック、実装済み／部分実装／未実装／対象外、形式・suffix制限、試験根拠 |
| [命令状況JSON](EZ80_INSTRUCTION_STATUS_R21_3.json) | 一覧の機械可読版、対象RTLのSHA256 |
| [デコード実装](EZ80_DECODE_IMPLEMENTATION_R21_3.md) | フェッチ時の保持、ページ・prefix・クラス分類、組合せmcode、実行と要求保持 |
| [最悪Setup経路](EZ80_WORST_SETUP_PATH_R21_3.md) | ISet[0]からRequest_Extended FFまでの合成後の全中間セル、遅延、CEと制約の考え方 |
| [Path1原文抜粋](R21_3_SETUP_PATH1.txt) | ユーザーアップロードのGOWIN .trから転記 |
| [Path1データ](R21_3_SETUP_PATH1.json) | 数値と転記元レポートSHA256 |
| [残りの工程](REMAINING_R21_3.md) | 8命令＋混在制御形式監査＋全体検証 |
| [R21.3配布時README](R21_3_README.md) | 当時のビルド・診断手順。現在の実機状態は本ファイルを優先 |

ISA_AUDIT_R21.jsonやREMAINING_R21.md等は過去版の監査。そこに残る「実機待ち」は当時の状態で、現在の判定は上のR21.3一覧を優先する。
この文書更新ではRTL・テストCOM・GPRJ・CST・SDCを変更していない。再ビルド不要。
