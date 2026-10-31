# MSXnano T80 eZ80 再構築 R2

R1でのGOWINビルド、SofaRun、スペースマンボウのプレイ、EZ80D1のPASSはユーザーによる実機確認済み。
R2では24bit INC/DECと、独立した24bit SP(SPL)を使う3バイトPUSH/POPを追加する。
PC・通常SP(SPS)・割込みは引き続きZ80の16bit動作。ADL命令フェッチはまだ追加しない。

## 実機手順

1. ZIPを新しいフォルダに完全展開する。
2. `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をGOWINで全ビルドする。
3. 配置配線・タイミング結果を確認してから、そのビットストリームを書き込む。
4. MSX-DOSから `hardware_test/EZ80D2.COM` を実行する。

期待する表示は `EZ80D2 R2: PASS`。
メモリの比較で不一致があれば、stageに加えて、24bit論理アドレス・期待値・実際の値を16進数で表示する。

```
EZ80D2 R2: FAIL stage 3
ADDR=030000 EXP=96 ACT=97
```

ADDRはテストが意図したCPU論理アドレス。SDRAM物理アドレスや実際の端子観測値ではない。
メモリに対応しないレジスタ単体の比較では `ADDR=------` と表示する。
通常は最初の不一致で停止して結果を表示する。正常時はPASSだけを表示する。

DI区間ではDOS/BIOSを呼ばない。結果と診断値を低位メモリに保存し、
拡張をロックしてから通常のZ80処理で16進数へ変換し、EI後にBDOS9で表示する。
DOS/BIOSがEIすることを許容し、表示後に拡張テストへ戻る経路はない。

R2のGOWIN・実機確認は未実施。詳細は `doc/RESTART_R2.md`。
