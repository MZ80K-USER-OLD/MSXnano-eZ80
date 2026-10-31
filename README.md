# MSXnano T80 eZ80 再構築 R3

R2のGOWINビルド、EZ80D2 PASS、その後のSofaRun・スペースマンボウのプレイはユーザー実機確認済み。
R3では24bit交換、SPへの転送、レジスタペアの複数バイト絶対メモリアクセスを追加する。
PCと通常SP(SPS)は16bitを維持。ADL命令フェッチとADL割込みはまだ追加しない。

## 実機確認

1. ZIPを新しいフォルダへ完全展開する。
2. `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をGOWINで全ビルドする。
3. 配置配線・タイミング結果を確認して、そのビットストリームを書き込む。
4. MSX-DOSで `hardware_test/EZ80D3.COM` を実行する。

正常時は `EZ80D3 R3: PASS`。
メモリ不一致時は最初の不一致について、stage、24bit論理アドレス、期待値、実際値を表示する。

```
EZ80D3 R3: FAIL stage A
ADDR=07FFFE EXP=56 ACT=57
```

ADDRはテストが意図したCPU論理アドレス。SDRAM物理アドレスや端子の観測値ではない。
レジスタ単体の比較ではADDR=------。正常時は各アクセスを逐次表示せずPASSだけを表示する。
DI区間ではDOS/BIOSを呼ばない。全テストを終えて拡張をロックし、通常Z80処理で診断を変換し、
EI後にBDOS9で結果表示する。システムコール内でEIする条件も検証する。

R3のGOWIN合成・配置配線・実機は未確認。
詳細は `doc/RESTART_R3.md`。過去版の説明書は履歴資料。
