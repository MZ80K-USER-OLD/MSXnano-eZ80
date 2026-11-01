# MSXnano T80 eZ80 再構築 R7

R6はGOWIN合成・実機の `EZ80BLK P1: PASS`・試験後のSofaRunからのスペースマンボウ起動／プレイをユーザー確認済み。R6のLUT使用率は報告値82％。
R7はMLT BC／DE／HL／SPを追加する。8bit×8bit→16bitの乗算器を1個共有し、DSPへの割当てを属性で指定する。
実際のDSP個数・LUT使用率・タイミングはGOWIN合成レポートで確認が必要。

## 実機確認

1. ZIPを新しいフォルダへ完全展開する。
2. `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をGOWINで全ビルドする。
3. LUT／DSP使用量と配置配線・タイミング結果を確認し、ビットストリームを書き込む。
4. 保存済みCOMをMSX-DOSで実行する。

```
EZ80MUL /RUN
```

期待表示は **EZ80MUL P1: PASS**。
FLASHまとめと同一のCOMなので再コピー不要。半角空白1つと大文字/RUNを指定する。
引数なしのPLANNED表示は機能試験の合格ではない。
不一致ではstageとADDR／EXP／ACTを表示する。
DI中はDOS／BIOSを呼ばず、通常SPSと拡張ロック状態を復元してからEI・BDOS表示・DOS復帰する。
その後、SofaRunからスペースマンボウを起動してプレイを確認する。

回帰には `EZ80MEM /RUN`、`EZ80ALU /RUN`、`EZ80BLK /RUN` も使える。
先行LEA／ADLの/RUNは対応RTLが完成してから実行する。
`sim/` 内のCOMはシミュレーション専用で、実機では実行しない。

I/O上位00h固定の追加命令は引き続き実装しない。通常Z80のI/O命令は維持する。
PC・割り込み用SPSは16bit、別SPLは24bit。ADL状態・24bit命令フェッチ・ADL割り込みは未実装。
詳細は `doc/RESTART_R7.md`、現行の機能検証集計は `verification_result.json`。
R7のGOWIN合成・配置配線・実機確認は未実施。
