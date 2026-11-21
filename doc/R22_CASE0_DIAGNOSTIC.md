# R22 CASE 0停止の切り分け — R22.1診断テスト

**FPGAは変更していません。GOWINの再ビルドは不要です。現在のR22で実行してください。**
R22のEZ80IOR /RUNがCASE 0だけを表示して停止し、RUNALL.BATにもFAILが出るとの実機報告を受けた切り分け用です。RUNALLの失敗命令・Stage・ADDR/EXP/ACTはまだ未確認です。原因の特定・RTL修正完了を意味する配布ではありません。

## 実行順

```
EZ80IR0 /RUN
EZ80IR1 /RUN
EZ80IR3 /RUN
```

| COM | 内容 | 最後の期待表示 | bytes | CRC32 |
| --- | --- | --- | ---: | --- |
| EZ80IR0.COM | 最初のケースと同じ準備・モード遷移・結果保存。INI2Rだけ同じ長さのNOP×2に置換 | EZ80IR0 R22.1: PASS | 6036 | 167DA27D |
| EZ80IR1.COM | INI2Rを1byte転送で終了。反復の再フェッチを行わない | EZ80IR1 R22.1: PASS | 5846 | F0DB0D2D |
| EZ80IR3.COM | CASE 0と同じINI2Rの3byte転送。16bit境界をまたぐ | EZ80IR3 R22.1: PASS | 6036 | 5E45384B |

3ファイルはZIPの直下とhardware_testに同一内容を収録。COMだけコピーすれば実行できます。/RUNなしはREADY表示だけ。旧FPGAや診断機能なしはNOT READY/UNSUPPORTEDになります。

## 進捗表示

```
CASE 0
RAM_OK
CODE_OK
ENTER_TEST
RETURN_OK
EZ80IR3 R22.1: PASS
```

- RAM_OK: 初期化したデータ領域を読み戻して一致を確認した後に表示。
- CODE_OK: 書き込んだ実行コード・復帰コードを全byte読み戻して一致を確認した後に表示。
- ENTER_TEST: 拡張空間へ入る前の表示。
- RETURN_OK: Z80/MSX側へ戻った後の表示。その後、保存したBC/DE/HL/AF・転送メモリ・SPLを比較。
- 不一致時はStage、ADDR、EXP、ACTを表示する。

表示は位置を絞る手がかりです。各表示の後にもDOS復帰、DI、再アンロック処理があるため、最後の表示だけで単一の回路を原因と断定しません。
DOS呼出し前にはZ80・MBASE=0・診断停止・拡張ロックへ戻し、呼出し直後にDIを再実行します。DOS/BIOS内部でEIが行われる条件を考慮しています。

報告してほしい情報は、各COMのPASS/FAIL、停止したCOM名と最後に表示された行、FAILの場合はADDR/EXP/ACTです。
全3本がPASSでも元のEZ80IOR全体の合格とはしません。元のCOMは53097bytes、この診断は約6KBであり、TPA占有量・配置・表示による時間差等も異なります。

## CASE 0の設定

開始Z80、MBASE=0E、幅prefixなし。BC=7A0003（有効カウンタは下位16bit）、DE=0066E4、HL=02FFFF。
入力ポート66E4→66E5→66E6、メモリ0EFFFF→0E0000→0E0001。
期待入力値3CはR22の内部診断ループバック。物理MSX I/Oへは出しません。
IR1はBC=7A0001で最初の1byteだけ。IR0は同じ準備を通り、INI2Rを実行しないため、BC/DE/HL/フラグと初期メモリを保持することを確認します。

## 検証

R22の全FPGAソース・GPRJ・タイミング制約が元ZIPとbyte単位で同一であることを確認。
3COMそれぞれの通常・CE停止/異なるクロック位相の6条件、結果保存値の故障注入1条件、実行コードの故障注入1条件、拡張無効・/RUNなし・旧機能識別・診断なしの4条件、計12プロファイルで期待結果一致。
CPUラッパ、ブリッジ、SDRAM制御RTLとSDRAMモデルを接続し、実COMを実行。DOSスタブ内部でEIとIM1割込みを実施。
コード故障は実行前に `ADDR=0E8200 EXP=5B ACT=5A` を表示して終了することを確認。

GOWIN・実機では未確認です。R22の実機CASE 0停止原因は未特定。Logic使用率やSetup/Hold改善を主張しません。

## ソース等

hardware_testにはCOM/hex/asm/vh/jsonと生成スクリプト、sim/toolsには試験コード、verificationには今回のログと集計を収録。
生成スクリプトはR22プロジェクトのhardware_testに置くと、既存build_data_r3.py/build_ior_r22.pyを参照して再生成できます。
再現用シミュレーションはR22プロジェクト上でCPUモデル生成後にtools/verify_ior_diag_r22_1.pyを実行します（GHDL/Icarusのパス設定が必要）。
