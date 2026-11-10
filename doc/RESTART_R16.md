# MSXnano T80 eZ80 restart R16 — HL間接のレジスタペア転送

実機確認済み・ユーザーがGitへコミットしたR15.3配布ソースを基準に、工程9のLDH系を追加します。ユーザー側Gitコミットのハッシュは取得していません。R15.3はCT1、D3、TST、MEM、RUNALL（LDH/LDXのみNOT READY）、SofaRunからスペースマンボウのPLAYまで確認済みです。

**R16のGOWIN合成・配置配線・実機確認は未実施です。LUT使用率、Fmax、タイミング収束は未計測です。**

## ビルドと実機試験

新しいフォルダへZIPを展開し、`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を再合成・配置配線してください。動作確認済みR15.3のソース・ビットストリーム・implを保存し、旧版の出力を書き込まないようにしてください。DualPin、言語設定、CST/SDCはR15.3と同一です。比較時は最適化設定もそろえ、Timing／Areaのどちらを使用したか記録してください。

実機を書き換えたら電源を入れ直し、最初に次を実行してください。

```text
EZ80LDH /RUN
```

期待表示は **`EZ80LDH P2: PASS`**。これは既に配布・FLASH保存済みのCOMです。既存20本と診断4本のCOMは同じバイト列のため、FLASH内のテスト更新は不要です。

続けて必要に応じて再起動を挟み、確認してください。

```text
EZ80CT1 /RUN
EZ80D3 /RUN
EZ80TST /RUN
EZ80MEM /RUN
RUNALL.BAT
```

CT1 R10:PASS、D3 R3:PASS、TST P2:PASS、MEM P1:PASSを期待します。**RUNALLではEZ80LDX P2:NOT READYだけが残り、ほかはPASSが期待結果です。** 最後にSOFARUNからスペースマンボウを起動・PLAYしてください。失敗した場合はStage、ADDR、EXP、ACT全文を記録してください。GOWINのLogic%、実LUT数、CLS数、Setup/HoldのSlackとimplも比較資料になります。

## 実装範囲

| レジスタ rr | LD rr,(HL) | LD (HL),rr |
| --- | --- | --- |
| BC | ED 07 | ED 0F |
| DE | ED 17 | ED 1F |
| HL | ED 27 | ED 2F |
| IX | ED 37 | ED 3F |
| IY | ED 31 | ED 3E |

拡張ゲート有効・Mode0・ED命令・割り込みサイクル以外で有効です。ゲートが閉じていれば従来の未定義NOPを維持します。リセットはZ80互換モード・拡張無効のままです。SPはこの命令群に含みません。

- Data_Longで2バイト／3バイトとデータアドレス幅を決定。40/52は短い転送、49/5Bは長い転送です。Stream_Longは別のフラグとして維持し、この命令には即値アドレスを追加しません。
- 短い転送はMBASE:HL[15:0]を使用し、FFFF→0000で同じMBASE内へ折り返します。長い転送はHL[23:0]を使用し、03FFFF→040000と桁上げします。
- バイト順は下位→中位→上位。F、アドレス用HL、転送元を意図せず更新しません。HLが転送先の場合は、元のアドレスを保持したまま各バイトを読みます。
- 短いロードの上位バイトは既存の実装に合わせ保持します。これを未定義上位ビットの一般的なISA保証とは扱いません。
- 機能マスクは診断あり83FF／なし03FF。C4=FF、C6=00。LDHのbit6を追加し、LDXのbit10は無効のままです。

旧検査ではED31もNOPを要求していたため、今回のLD IY,(HL)として検査範囲を更新しました。ED31の新しい行にI/O要求を追加していないことを確認し、IN0/OUT0/TSTIO等を追加しない方針を維持しています。

オペコード表は既存P2試験データとGNU binutilsのeZ80アセンブラ実装で照合しています。参考： https://gnu.googlesource.com/binutils-gdb/+/3fb6f5457e5b53fdb73a98a24b3764e821e8ccc5/gas/config/tc-z80.c （emit_ld_rr_m／emit_ld_m_rr）。

## 回路共用

| 対象 | R16の実装 |
| --- | --- |
| 転送アドレス | 既存EX_SP_Address 24bitを共用 |
| 書込元の保持 | 既存EX_SP_Source 24bitを共用 |
| アドレス加算 | EX_SP_Address_Nextの24bit +1を共用し、短い転送は下位16bitだけ更新 |
| 下位2バイトの読出し書込 | 既存DI_Reg／Read_To_Reg／レジスタファイルを使用 |
| 上位バイト | 既存Upper_Portのイベント0へ統合 |
| レジスタ選択保持 | 既存RegAddrA_rを使用 |
| 転送進行 | 既存MCycle/TStateを使用。新しいカウンタ・FSM状態を追加しない |

新規のワークレジスタ、制御FF、ALU、乗算器は追加していません。ただし追加デコードと選択回路は必要なため、LUT増加がゼロになるとは保証しません。実際の規模はGOWINで比較してください。

要求アドレスと書込データは従来のAddress_Reg／Address_Bank_Reg／Data_Out_Regを通します。アドレス作業値の進行は、WAITを通過したデータT2だけで行います。CPU停止中の再進行を防ぎます。

16bit MSXバスと24bit拡張バスの分離、拡張アクセス時のMSX側遮断、16bitバスだけによるFFFFセカンダリスロット判定を維持しています。ラッパの変更は機能マスクの2定数だけです。SDRAM、ブリッジ、top、VDP、PAL/YJK、GPRJ、CST、SDC、ALU、レジスタファイルはR15.3から変更していません。

## 割り込み受付と最終バイト

追加したEI直後のLDH試験で、配布前のR16実装に問題を検出しました。最終バイトの書込みは次のM1/T1で完了しますが、割り込み受付によってPair_Indirectが先に無効になると、転送先選択がHLへ戻ってしまいました。試験では期待56に対しB2が残りました。

既存のRegAddrA_rへ命令中の転送先を保持し、割り込み受付後の遅延書込みも同じレジスタへ到達するよう修正しました。新しい保持レジスタは追加していません。この問題は新規LDH実装を配布前に検出したもので、R15.3で実機報告された不具合とは分けて記録しています。検出ログはdoc/R16_PRE_RELEASE_IRQ_FAILURE.logです。

## 検証

- 最終ソースで597シナリオ（故障注入を含む）と別枠の期待失敗24シナリオを実行。
- R15.3のデコーダ・Write分類関数を参照し、8388608入力組合せを走査。今回の新しい10個のEDオペコードが有効となる2560組合せだけを除き、8386048組合せで全49出力を照合。拡張無効、Mode0以外、IRQ/NMI、他命令は比較対象に含みます。
- F／XY／IMの値は変化させていますが、すべてを独立に組み合わせた形式証明ではありません。
- 既存EZ80LDH.COMの20ケースを含む7プロファイルを実行。2/3バイト、全5ペア、HL自身を含む重複、FLAGS、位相差、WAIT、CPU停止、拡張なし、/RUNなし、故障時のADDR/EXP/ACTを検証。
- 内部単体試験は40命令ケースを通常・WAIT・CPU停止条件で実行。4種類の幅プレフィクス、長い桁上げ、短い折返し、全5ペア、F保持を確認。EI後のIM1と転送中に要求したNMIについても各40命令を実行し、復帰後のデータを確認。
- MBASE=0Eで短いLDHを実行し、HL上位03を無視して0EFFFF→0E0000へ折り返すこと、0F0000や3バイト目を壊さないこと、HL自身へのロードを検証。
- MEM/ALU/BLK/MUL/LEA/FETCH/制御/IRQ/NMI/MBASE/MADL/混在/TST、EX(SP)共用、要求保持、実際のセカンダリスロットRTLも回帰確認。
- 診断COMではDOSがEIする条件を含め、DOS呼出しはZ80・MBASE0・拡張ゲート閉鎖、戻り直後DIで実行。

単体試験の短いFFFFアクセスはフラットRAMモデルでのCPU検証です。実機のFFFFはセカンダリスロットレジスタであり、既存実機COMの短い転送は予約した安全な低RAMを使用します。完全なMSX BIOS/DOSやボード全体、配置配線後の遅延はシミュレーションしていません。タイミング制約を緩めて違反を消す変更も行っていません。

再実行入口：`python tools/verify_r16.py`。GHDL、Icarus Verilogを使用し、GHDL/IVERILOG/IVL_ROOT/VVPで環境を指定できます。比較基準はdoc/r15_3_baseline、差分はdoc/R16_LDH.patchです。今回の結果はverification_result.json、個別結果はverification_groups、ログはverification_logsです。過去のtools/docは履歴であり、今回の入口は本READMEとverify_r16.pyです。

## 残る工程

工程9の次はLDX（IX/IY変位付きペア転送）です。工程7/8のADL IM0、MADL/混在RST等の残項目、命令別監査、工程10のタイミング・規模・最終実機検証も残ります。RUNALLのNOT READYが1本になっても全eZ80命令の完成とは扱いません。IN0/OUT0/TSTIO等の上位I/Oを00固定する追加命令は実装しない方針を維持します。

## COM CRC32

| COM | bytes | CRC32 |
| --- | ---: | --- |
| EZ80LDH.COM | 10981 | 0FDF3B53 |
| EZ80LDX.COM | 21810 | CF2B63CE |
| EZ80CT1.COM | 23697 | EE98260C |
| EZ80D3.COM | 18896 | 14B01ADC |
| EZ80TST.COM | 12968 | 08ADDC8B |
| EZ80MEM.COM | 2268 | 0C7D91D6 |
