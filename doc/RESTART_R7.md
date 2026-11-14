# 再構築R7：MLTと共有DSP乗算器

## 基準と変更範囲

R6のGOWIN合成成功、実機起動、`EZ80BLK P1: PASS`、その後SofaRunからスペースマンボウを起動・プレイできたことをユーザー報告として記録する。R6のLUT使用率はユーザー報告82％。配置配線・タイミング・DSP内訳のレポート本体は未取得。

R7で変更するFPGAファイルは `fpga/G80A_eZ80/t80_ez80.vhd` と `t80_mcode_ez80.vhd` の2つ。
元G80A、R6のIRQ応答修正を含むラッパー、メモリブリッジ、SDRAM、トップ、GPRJ、Dual Purpose Pin／SystemVerilog設定、CST、SDCはR6と同一。
タイミングのmulticycleやfalse_pathを追加しない。
R7のGOWIN合成・配置配線・実機動作は未確認。

## 工程の位置

R3完了後の実装順を起点にすると、R4メモリ、R5算術、R6ブロック、R7乗算で、現在は4番目。
これはR版番号とは別の数え方であり、以前の全工程表を照合して確定した総工程数ではない。
R7の次はLEA／PEA、その後にADLのフェッチ・制御移行・割り込み・混在動作の検証が残る。

## 命令の範囲

| 命令 | 入力と結果 | 保持するもの |
|---|---|---|
| MLT BC（ED 4C） | B×CをBC下位16bitへ | BCU、A、F、他のペア |
| MLT DE（ED 5C） | D×EをDE下位16bitへ | DEU、A、F、他のペア |
| MLT HL（ED 6C） | H×LをHL下位16bitへ | HLU、A、F、他のペア |
| MLT SP（ED 7C）短い指定／通常Z80 | SPSの上位バイト×下位バイトをSPSへ | SPL、A、F |
| MLT.L SP（49 ED 7C） | SPL下位16bitの両バイトを乗算し、下位16bitへ | SPL上位8bit、SPS、A、F |

いずれも符号なし8bit×8bit→16bit。24bit×24bitや16bit×16bit乗算を追加したものではない。
R7はPC=16bit、SPS=16bit、SPL=24bitのまま。ADL状態、命令フェッチ24bit化、ADL CALL／RET／割り込みはまだ未実装。
BC／DE／HLのMLTでは上位8bitを保持し、長い指定でも16bitの積だけを反映する。
SPの選択はデータ幅による。40h／52h／プレフィクスなしはSPS、49h／5BhはSPL。
表裏のBC／DE／HLは元T80のEXX選択に従う。

公式eZ80 CPU User Manual UM007715-0415、MLT rr／MLT SP（246–247ページ）：
https://www.zilog.com/docs/UM0077.pdf

拡張ゲートを開いたときだけMLTとして解釈する。
ロック中は元Z80の未文書NEG別名を維持する。これらのオペコードをロック中に実行してもMLTは使えない。
拡張ゲートのE1h応答だけでは、個別命令の実装範囲を識別できない。

## LUTとDSP

各命令で共通の8bit入力レジスタ2本と16bit積レジスタを使う。
乗算式は `Mul_Left * Mul_Right` の1箇所のみ。演算対象ごとに別の乗算器を持たせない。
積レジスタにGOWINの `syn_dspstyle="dsp"` 属性を付け、LUT乗算器ではなくDSPハードウェアへの割当てを指定する。

GowinSynthesis User Guide SUG550、syn_dspstyle：
https://cdn.gowinsemi.com.cn/SUG550E.pdf

これはRTL上の指定であり、実際のDSPプリミティブ個数やLUT使用率を測定した値ではない。
R6の82％を基準に、R7の合成レポートでDSP使用量・乗算器の実装先・LUT使用率を比較する。
GHDLの機能検証ではこのベンダ属性を解釈しないため、unhandled attribute警告が出る。GOWINでの属性の有効性やDSP配置の成立を代わりに証明するものではない。
GHDL変換後のCPUでは符号なし乗算演算子が1個であることも確認する。

## 捕捉、WAIT、CPU停止、IRQ

| 反映点 | 動作 |
|---|---|
| 命令フェッチM1／T2 | 従来のWAIT受付。WAIT解除までフェッチを保持 |
| M1／T4 | 選択したレジスタ／スタックの両8bitオペランドを捕捉 |
| M1／T5 | 捕捉値から積を登録 |
| M1／T7 | 選択したペアまたはSPS／SPLの下位16bitへ1回だけ反映 |
| 命令終了 | 演算結果の反映後に保留IRQを受け付ける |

T4からT7は外部データアクセスを伴わない内部演算。
WAITはこのM1のT4–T7を停止しない。内部演算中にWAITをLowにしても、従来T80の受付点以外では停止しない。
一方CEN停止では、オペランド捕捉、積登録、結果反映がすべて停止する。
CPU停止は立上り／立下りの許可をT-state全期間単位で対にする。
WAITとCENを同一の停止機構として扱わない。

IRQ試験ではMLTのT5でINTを入れ、T7反映前には割り込みへ移行しないことを確認する。
復帰PCはMLTの次の命令。MLTを再実行するために戻してはならない。
SPSへ2バイトのPCを保存し、通常Z80 IM1ハンドラからEI／RETIで戻る。
ADL割り込み・IM0／IM2／NMIの試験ではない。
T-stateの数はT80バスに合わせた本実装の値で、実eZ80の実行サイクル数と一致させたという意味ではない。
実機のsetup/holdはGOWIN配置配線後のレポートで確認する。

## 実機用COM

FLASHまとめの `EZ80MUL.COM` を変更せず使用する。再コピー不要。
3503バイト。SHA256：
`accc1d7c5328e0be328016737767c05e8fd91faba85a861a9872867b21b3b381`

```
EZ80MUL /RUN
```

期待表示は **`EZ80MUL P1: PASS`**。
引数なしのPLANNED表示は機能試験の合格ではない。半角空白1つと大文字/RUNを指定する。
BC／DE／HLで0×255、1×255、16×16、127×129、255×255を試す15件と、
SPL／SPSの各0102h・1020h・FFFFhの6件、合計21件。
積の下位2バイトと文書化されたフラグを検査する。この既存COMでは上位8bitの保持を検査しないため、内部追加試験で補う。

不一致時はstageと `ADDR=xxxxxx EXP=xx ACT=xx` を表示する。
アドレスは結果の低位SNAPまたはFLAGSなどの論理アドレスで、SDRAM端子の波形ではない。
破損注入では `FAIL stage 1`、`ADDR=000EA6 EXP=00 ACT=01` を確認する。

試験はDI中にDOS／BIOSを呼ばない。SPSを計算対象にする場合は、結果を保存し、通常SPSを復元してからPUSH／POPでフラグを保存する。
終了時は拡張をロックし、SPSとIX／IYを復旧してからEI・BDOS表示・DOS復帰する。
BDOSモデル自体がEIすることを許容している。
このCOMの結果退避は低位メモリと通常スタックだけ。専用拡張RAM・MegaRAM・VRAMへMLTの積を書き込む試験ではない。
試験後にSofaRunからスペースマンボウを起動・プレイして通常動作を確認する。

## 追加試験と回帰

現行集計は `verification_result.json`。

- R6までの回帰56条件（内部ブロックIRQ／WAIT、通常I/O、保存済みCOM、故障注入診断を含む）。
- 保存済みEZ80MUL.COM実行6条件：正常4位相、SNAP破損、拡張無効。
- 内部MLT試験4条件：通常、フェッチWAIT、CEN停止、組合せ。後3条件では内部演算中のWAIT Lowも追加。
- R6由来の期待失敗2条件：幅再取得欠落と割り込み応答抑止を検出。

内部試験は各条件でMLT 71件。BC／DE／HL×5幅指定×2入力×表裏2組の60件、SPS／SPL選択10件、IRQ中断1件。
独立したPython整数積を期待値に使い、F全8bitとA、上位8bit、非対象ペアの保持を検査する。
0・1・符号境界・最大値などを含む固定シードの値を使うが、65536通りの全入力組合せを網羅した試験ではない。
加えてロック中の4つのNEG別名を確認する。
各命令の入力捕捉・積登録・反映の回数が各71であることを検査し、CEN停止時の重複反映を検出する。
IM1の実際のベクタ遷移、応答、SPSフレームと復帰先も確認する。

`sim/mul_corners/EZ80M7.COM` は固定SPS・仮想0038hベクタのシミュレーション専用。
**実機で実行せず、FLASHへの追加保存もしない。**
実機用は保存済みEZ80MUL.COMを使う。
GHDL・Icarus Verilog・簡易BDOS9・SDRAMモデルの機能試験であり、実MSX-DOS全体やBIOS起動、映像、配置配線後の遅延を再現しない。

## 除外する追加I/O命令

I/OポートA[15:8]を00hに固定する追加命令は実装対象から除外する。
IN0／OUT0、INIM／INDMと反復版、OTIM／OTDMと反復版、TSTIOの専用実装を追加しない。
通常Z80のIN／OUT・INI／IND／INIR／INDR・OUTI／OUTD／OTIR／OTDRは維持する。
未実装命令のオペコードに例外を発生させる仕組みは追加していない。元Z80のNOPや別名として解釈される場合がある。
R7のMLT追加はこの除外方針を変更しない。`tools/verify_scope_r7.py` で追加I/O要求がないことと除外命令のデコードを確認する。

## 再生成

```
python3 tools/rebuild_from_t80.py
python3 tools/extend_r2.py
python3 tools/extend_r3.py
python3 tools/extend_r4.py
python3 tools/extend_r5.py
python3 tools/extend_r6.py
python3 tools/extend_r7.py
bash tools/run_checks.sh
```

GHDL／IVERILOG／IVL_ROOT／VVP環境変数で実行ファイルを指定できる。
ビルドするプロジェクトは `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`。
過去のRESTART_R1..R6は各版の公開時点の記録。今回の実機基準と未確認範囲は本書を優先する。
