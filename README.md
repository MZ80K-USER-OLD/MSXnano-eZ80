# MSXnano T80 eZ80 再構築 R6

R5はGOWIN合成成功、実機の `EZ80ALU P1: PASS` と、その後のSofaRun・スペースマンボウのプレイをユーザー確認済み。
R6は24bitのLDI／LDD／LDIR／LDDR／CPI／CPD／CPIR／CPDRを追加する。
PC・割り込み用SPSは16bit、SPLは24bit。ADLモードはまだ未実装。

## 実機確認

1. ZIPを新しいフォルダへ完全展開する。
2. `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をGOWINで全ビルドする。
3. 配置配線・タイミング結果を確認し、ビットストリームを書き込む。
4. MSX-DOSで保存済みのCOMを実行する。

```
EZ80BLK /RUN
```

期待表示は **EZ80BLK P1: PASS**。
FLASHまとめのEZ80BLK.COMとバイト列は同じ。再コピー不要。
半角空白1つと大文字 `/RUN` で指定する。引数なしのPLANNEDは機能試験の合格ではない。
不一致時はstageと `ADDR=xxxxxx EXP=xx ACT=xx` を表示する。
DI中にDOS／BIOSを呼ばず、拡張をロックしてから診断表示・EI・DOS復帰する。
PASS後にSofaRunからスペースマンボウを起動して通常動作を確認する。

回帰用の `EZ80MEM /RUN` と `EZ80ALU /RUN` も利用できる。
MUL／LEA／ADLの先行COMは対応するRTLができてから `/RUN` する。
`sim/` 内のCOMは固定メモリ・仮想割り込みベクタを使うため、実機で実行しない。

## ループとIRQ／WAIT

1バイトの処理を終えた区切りで割り込みを受け付ける。
繰返し継続時は幅プレフィクスの先頭へ、終了時は次の命令へ戻る。
WAITでT2が保持される間はアドレス・データ・レジスタを保持し、重複更新を防ぐ。
従来ラッパーの割り込み応答IORQ抑止もeZ80側で修正した。

詳細・試験条件・未実装範囲は `doc/RESTART_R6.md`、現行集計は `verification_result.json` を参照。
R6のGOWIN合成・配置配線・実機動作は未確認。
