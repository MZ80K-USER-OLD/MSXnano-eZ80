# MSXnano T80 eZ80 restart R15.3 — TSTデコード統合・回帰比較版

R14で同一のEZ80CT1.COMがPASSし、R15では実行前の照合でFAILした実機結果を受けた比較修正版です。TSTの機能を維持し、R15で追加したデコードの置き方を変更しています。

**実機の原因や修正完了を確定した版ではありません。R15と同じ機能を保つことをシミュレーションで確認しましたが、R15.3のGOWIN合成・配置配線・実機確認は未実施です。**

## 最初に実機で確認するもの

GOWINプロジェクト：

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

古いimpl・レポート・動作確認済みR14ビットストリームは別の場所に保存し、このZIPを新しいフォルダへ展開して再合成・配置配線してください。過去版の出力をそのまま書き込まないよう、GOWINが今回のソースを再読込したことを確認してください。

R15.3を書き込んだら電源を入れ直し、**R14でPASSしたものと同じEZ80CT1.COM**を最初に実行してください。

```text
EZ80CT1 /RUN
```

期待表示：`EZ80CT1 R10: PASS`。R10は元の制御試験の版を示すため、そのままです。Stage Vで失敗したら、ADDR／EXP／ACT全文を記録してください。停止なら最後のSTART／LOAD／VERIFY／RUN／CHECKを記録してください。

続けて再起動を挟み、次を確認してください。

```text
EZ80D3 /RUN
EZ80TST /RUN
EZ80MEM /RUN
RUNALL.BAT
```

期待値はD3 R3:PASS、TST P2:PASS、MEM P1:PASSです。RUNALLのNOT READYはEZ80LDH／EZ80LDXの2本、それ以外はPASSです。最後にSOFARUNからスペースマンボウを起動・PLAYしてください。GOWINの実LUT数、CLS数とimpl ZIPも比較に使用します。

**既存20本のCOMと、R15.1/R15.2の4本の診断COMは同一バイト列です。FLASH内のCOM更新は不要です。** ZIP直下・プロジェクト直下・hardware_testに計24種類を同一内容で収録しています。

## 実機で判明したこと

| 条件 | 結果 |
| --- | --- |
| R15再ビルド後のEZ80TST | PASS |
| R15のEZ80MEM | PASS |
| R15のEZ80MX1、EZ80TS1、EZ80BN1 | PASS |
| R15の元EZ80D3 | Stage3 ADDR=030000 EXP=96 ACT=97 |
| R15の元EZ80CTL | フリーズ |
| R15のEZ80CT1 | Stage V ADDR=09004B EXP=00 ACT=01 |
| R14で同じEZ80CT1 | PASS |

EZ80CT1は、ADLコードを実行する前に090000以降の1674バイトを読み戻し、COM内の期待値と比較します。090049～09004CはC3 51 00 09、すなわちJP 090051です。09004Bが01として命令フェッチされるとJP 090151へ変わるため、元CTLのフリーズを説明し得ます。ただし、実機報告だけでは転送、RAM、読み出し、照合結果の保存のどこで不一致が生じたかまでは確定していません。

R14とR15の比較から、R15で導入された回帰の可能性が明確になりました。TST追加が無関係な命令の論理動作を変えたのか、合成・配置配線でタイミングが変わったのかは未確定です。R15.3は後者も含めて比較するための構成変更です。

## FPGAの変更

R15から変えたFPGAファイルは **fpga/G80A_eZ80/t80_mcode_ez80.vhdの1本だけ**です。

R15では、主デコード末尾にTSTの判定を追加し、MCycles、読出先、ALU選択、アドレス選択等を一括して上書きしていました。R15.3は次の構造にしています。

| 項目 | R15.3 |
| --- | --- |
| TST A,r / TST A,(HL) | 従来のED opcode case内に専用行を配置 |
| TST A,n（ED64） | NEG別名の行で、拡張有効時だけTSTを選択 |
| 拡張無効時 | ED04～3Cの未定義NOP、ED64のNEG別名を維持 |
| AND演算とフラグ | 既存ALUを共用、変更なし |
| A／ソースへの書戻し | 既存の書戻し禁止状態を維持 |
| 命令識別 | 組合せのTst_Active判定を共用。新規制御FFなし |
| 共有XYサイクル末尾 | MC6/MC7でTSTのアドレス・入力バス・Inc_PC/NoReadを上書きしないよう限定。TStatesは従来どおり |
| 最終Writeプロセス | R15と完全同一 |

TSTはMCyclesが1または2の命令ですが、到達しないMC6/MC7も含めてR15と全49制御出力が一致するようにしています。不要なケースをdon't-careとして除外していません。マトリックス版R14.1は使用していません。

CPU本体、PC／SPS／SPL、ALU、レジスタファイル、pack、ラッパ、16bit MSXバスと24bit拡張バスの分離、$FFFF遮断、ブリッジ、SDRAM、VDP、PAL/YJK、GPRJ、CST、SDCはR15と同一です。DualPinと言語設定も変更していません。新しいワークレジスタ・FSM状態・演算器は追加していません。

機能マスクは診断あり83BF／なし03BF、C4=BF、C6=40のままです。TSTIO/IN0/OUT0等の上位I/Oを00固定する追加命令は実装していません。

## 検証

- R15の実ソースを参照CPUデコーダとして使用し、8388608入力組合せで全49制御出力を比較。一切のTST除外なし。Mode0～3、全opcode/ISet/MCycle、拡張、幅、ADL、サフィックス、分岐成立、IRQ/NMIのプロファイルを走査。
- F、XY、IMは走査中に値を変えていますが、すべての独立組合せを網羅した形式証明ではありません。
- 異常なWrite_Classを与えると比較が失敗することも確認。
- 全体585シナリオ（診断用の故障注入も含む）と、別枠の期待失敗24シナリオを実行。
- MEM、ALU、BLK、MUL、LEA、FETCH、PC境界、制御命令、IRQ/NMI、MBASE、MADL、混在CALL/RET、TSTの回帰を実施。
- 元のEZ80D3/EZ80CTL、診断あり／なしの実COM、R15.1の7診断条件、R15.2の8診断条件を実行。通常Z80 IRQ、DOSがEIする条件、WAIT、CEN停止、位相差も含む。
- R15.2のコード照合は、転送命令を31→30に壊すとStage Vで止まり、ADL実行を始めないことも確認。
- 元の20COMと4診断COMはハッシュで同一性を検証。

完全なMSX BIOS/DOS、ボード全体、配置配線後の遅延をシミュレーションしたものではありません。R15.3のLUT数、デコード段数、Fmaxの改善も未計測です。構成変更で必ずLUTが減る、または実機回帰が直ると主張するものではありません。

再実行：`python tools/verify_r15_3.py`。GHDL、Icarus Verilog、patchを使用し、GHDL/IVERILOG/IVL_ROOT/VVPで環境を指定できます。今回の集約結果はverification_result.json、個別結果はverification_groups、実行ログはverification_logsに収録しています。

R15からの差分はdoc/R15_3_TST_DECODE.patch、再適用入口はtools/extend_decode_r15_3.py。比較基準のCPUソースはdoc/r15_decode_baselineに保存しています。以前のdoc・ツールは経緯確認用です。今回の入口はREADMEとRESTART_R15_3.md、verify_r15_3.pyです。

## タイミング・規模

| 実機レポート | 通常R14 | R15 |
| --- | ---: | ---: |
| LUT | 16647 | 16819 |
| Logic | 18878 | 19050 |
| CLS | 10047 | 10092 |
| 54MHz系Fmax | 33.854MHz | 37.686MHz |

両版とも表示上はLogic 92%です。R15ではSetup違反端点595、Hold違反端点42。R15の要求アドレスへのSetupは−3.772ns、書込指定へのSetupは−3.457nsの掲載経路があります。

通常MSX側sdram_din_latched bit0のHold違反を、そのまま拡張RAM側の原因と決めつけません。拡張側はext_data_latchedを選ぶ構成です。CPUイネーブルの間引きだけを根拠にSetup/Holdを無効とは扱いません。捕捉タイミングと保持期間を確認できる経路だけを個別に評価する方針で、今回は制約の追加・緩和を行っていません。

R15.3の実機試験後も再ビルドで結果が変わる場合は、単発PASSだけで完了とはせず、配置配線・クロック・保持条件を引き続き調べます。戻す際は、動作確認済みのR14ビットストリームを使用してください。

## COM CRC32

| COM | bytes | CRC32 |
| --- | ---: | --- |
| EZ80CT1.COM | 23697 | EE98260C |
| EZ80BN1.COM | 8051 | 67F89986 |
| EZ80TS1.COM | 15338 | 95020F33 |
| EZ80MX1.COM | 9722 | 48AB4663 |
| EZ80CTL.COM | 23296 | 70955055 |
| EZ80D3.COM | 18896 | 14B01ADC |
| EZ80TST.COM | 12968 | 08ADDC8B |
