# R24.2 レジスタ選択共通化・比較候補

R24.2の実機確認結果を基準とする、面積比較用の候補です。正式なR24.3ではありません。

HL→IX/IYの選択番号生成を共有しました。追加FFなし。A/B/C/U読み出しポート数は変更していません。
LUT削減量・GOWINタイミング・この候補の実機動作は未確認です。

* 検討内容：[doc/R24_2_REGSEL_REVIEW.md](doc/R24_2_REGSEL_REVIEW.md)
* 変更差分：[doc/R24_2_REGSEL_COMPARE.patch](doc/R24_2_REGSEL_COMPARE.patch)
* 検証結果：[verification_regsel_compare/result.json](verification_regsel_compare/result.json)
* 比較検証：`python3 tools/verify_regsel_compare.py`
* GOWINプロジェクト：`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

基準R24.2と同じGOWIN設定でビルドし、Logic実数、LUT/ALU、FF、CLS、Setup/Holdを比較してください。
Logic表示だけでは小さな差を判断できません。増える場合は基準R24.2を使用してください。

既存COM 34本はR24.2と同一です。新たにFLASHへ書き込むテストはありません。
面積比較で採用候補になった場合の実機確認：EZ80MEM /RUN、EZ80MR4 /RUN、EZ80LDH /RUN、EZ80LDX /RUN、RUNALL.BAT、SOFARUNからスペースマンボウの起動・PLAY。

`verification_r24_2`と従来のrelease検証ログは基準版の記録です。本候補の検証結果と混同しないでください。
元のREADMEはdoc/R24_2_BASELINE_README.mdへ保存しました。
