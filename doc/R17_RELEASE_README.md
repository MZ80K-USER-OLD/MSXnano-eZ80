# MSXnano T80 eZ80 restart R17 — IX/IY変位付きレジスタペア転送

実機確認済みR16を基準に、工程9のLDX系を追加します。LDXはテスト名であり、単独の命令名ではありません。対象はLD rr,(IX/IY+d)とLD (IX/IY+d),rrの2/3バイト転送です。

**R17のGOWIN合成・配置配線・実機動作・LUT数・タイミング収束は未確認です。** R16はGOWIN合成成功、Logic93%、LDH/CT1/D3/TST/MEM、RUNALL（LDXだけNOT READY）、SofaRunからスペースマンボウの起動・PLAYまで確認済みです。

## ビルドと実機試験

動作確認済みR16のソース・ビットストリーム・implを保存し、R17は新しいフォルダへ展開してください。プロジェクトはこれまでと同じです。

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

旧版のimplを再利用せず、今回のソースを再合成・配置配線してください。GPRJ、DualPin、言語設定、CST/SDCはR16と同一です。比較用にTiming/Area設定もそろえてください。R16の最適化設定は未報告のため、今回使った設定も記録してください。

実機を書き換えて電源を入れ直し、最初に実行してください。

```text
EZ80LDX /RUN
```

期待表示は **`EZ80LDX P2: PASS`** です。続けて確認してください。

```text
EZ80LDH /RUN
EZ80CT1 /RUN
EZ80D3 /RUN
EZ80TST /RUN
EZ80MEM /RUN
RUNALL.BAT
```

期待値はLDH P2:PASS、CT1 R10:PASS、D3 R3:PASS、TST P2:PASS、MEM P1:PASSです。**今回からRUNALLの全テストでPASSを期待し、NOT READYは残りません。** 最後にSofaRunからスペースマンボウを起動・PLAYしてください。必要に応じて各試験の前に再起動してください。失敗時はStage、ADDR、EXP、ACT全文を記録してください。

既存20本とR15.1/R15.2診断4本、計24本のCOMはR16と同じバイト列です。**FLASH内のCOMの更新は不要です。** ZIP直下・プロジェクト直下・hardware_testに同じ内容を収録しています。GOWINのLogic%、実LUT数、CLS数、Setup/HoldのSlack、implも比較資料になります。

## 命令とオペコード

各表の末尾に符号付き8bit変位d（-128～127）が1バイト続きます。

| rr | LD rr,(IX+d) | LD (IX+d),rr | LD rr,(IY+d) | LD (IY+d),rr |
| --- | --- | --- | --- | --- |
| BC | DD 07 d | DD 0F d | FD 07 d | FD 0F d |
| DE | DD 17 d | DD 1F d | FD 17 d | FD 1F d |
| HL | DD 27 d | DD 2F d | FD 27 d | FD 2F d |
| IX | DD 37 d | DD 3F d | FD 31 d | FD 3E d |
| IY | DD 31 d | DD 3E d | FD 37 d | FD 3F d |

オペコードは既存EZ80LDXの40ケースとGNU binutilsのeZ80アセンブラ実装（emit_ld_rr_m／emit_ld_m_rr）で照合しています。
参考： https://gnu.googlesource.com/binutils-gdb/+/3fb6f5457e5b53fdb73a98a24b3764e821e8ccc5/gas/config/tc-z80.c

Data_Long=0では2バイトを転送し、MBASE:IX/IY[15:0]を使用します。変位計算とバイト進行は16bitで折り返し、MBASEを保持します。Data_Long=1では3バイトを転送し、IX/IYの全24bitへ符号拡張したdを加え、バイト進行も24bitで行います。

40/52は短い転送、49/5Bは長い転送です。Stream_Longは独立して維持しますが、この命令群の変位は常に1バイトで、余分な即値バイトを消費しません。SPは転送対象に含みません。Fは保持します。短いロードの上位バイトは現実装では保持しますが、未定義上位ビットに対する一般的なISA保証として扱いません。

新しいデコードは拡張ゲート有効・Mode0・ISet=00・DD/FD状態・IRQ/NMIサイクル以外でだけ有効です。ゲートを閉じた通常MSX動作では、元のZ80のDD/FD付き命令・別名動作を維持します。CB/ED側の命令はこの追加デコードの対象ではありません。

## データ経路と回路共用

| 対象 | R17の実装 |
| --- | --- |
| 変位加算 | 既存Indexed_Addressの24bit加算器を共用 |
| 有効アドレス保持 | LDH/EX(SP)のEX_SP_Address 24bitを共用 |
| 書込元の保持 | LDH/EX(SP)のEX_SP_Source 24bitを共用 |
| バイト進行 | 既存EX_SP_Address_Nextの24bit +1を共用 |
| 下位2バイトの読出し書込 | 既存DI_Reg、Read_To_Reg、レジスタファイルを共用 |
| 上位バイト書込み | 既存Upper_Portのイベント0を共用 |
| 最終バイトの転送先保持 | 既存RegAddrA_rを共用 |
| 進行制御 | 既存MCycle/TState、変位読出し1サイクル＋データ2/3サイクル |

新しいワークレジスタ、カウンタ、FSM状態、ALUは追加していません。新規のフリップフロップをRTLに追加しない構成ですが、追加デコード・選択回路によるLUT増加や、GOWIN最適化時の回路複製がゼロになるとは保証しません。規模・段数・遅延はGOWINで確認してください。

旧ローテート、DAA/CPL/SCF/CCF、LD SP,nn、LD A,nへ入る前に、基本命令デコード内でLDXの分岐を選びます。この命令の間は旧自動XYフェッチと即値ロードの追加処理を通しません。変位はM2で読み、T3で既存加算器の結果を保持し、T4でデータ要求用のアドレスへラッチします。

DD/FD31はLD SP,nnではありません。SPLの即値上位ロード処理をLDX中は抑止します。DDとFDでIX/IYの転送対象が入れ替わる31/37、3E/3Fも区別しています。

転送先がアドレス元と同じIX/IYでも、途中で更新されたレジスタから次のアドレスを作り直しません。書込みも命令開始時の値を保持してから転送します。RegAddrA_rへの転送先保持は旧XYのレジスタ置換より優先し、最終バイトの遅延書込みがIRQ/NMI受付後も同じレジスタへ届くようにしています。

## WAIT、割り込み、バス分離

要求は従来のAddress_Reg／Address_Bank_Reg／Data_Out_Regとラッパの保持回路を通します。アドレス作業値のバイト進行はClkEnとWAITを通過したデータT2でだけ行い、CPU停止やWAIT中に二重に進めません。変位取得や複数バイト転送の途中ではIRQ/NMIを受け付けず、命令完了後に受け付けます。

16bit MSXバスと24bit拡張バスの分離、拡張アクセス時のMSX側遮断、16bitバスだけによるFFFFセカンダリスロット判定を維持します。ラッパの変更は機能マスク定数のみです。診断あり87FF／なし07FF、C4=FF、C6=00、C5=87/07、C7=78/F8です。

CPU core、mcode、ラッパの計3ファイルが変更対象です。pack、ALU、レジスタファイル、top、ブリッジ、SDRAM、VDP、PAL/YJK、GPRJ、CST、SDCはR16と同一です。IN0/OUT0/TSTIO等の上位I/Oを00固定する追加命令は実装しません。タイミング違反を消すための一律の制約緩和も行いません。

## 検証

最終ソースで616シナリオ（デコーダ比較・故障注入を含む）と別枠の期待失敗24シナリオを実行しています。

- R16の実デコーダとWrite分類関数を参照し、8388608入力組合せを走査。新しいDD/FDペア命令が有効になる1920組合せだけを除き、8386688組合せで全49出力を比較。拡張無効、他命令、CB/ED、Mode0以外、IRQ/NMIのプロファイルは比較対象です。F、XY、IMは値を変えていますが、すべてを独立に組み合わせた形式証明ではありません。
- 既存EZ80LDX.COMの40ケースを7プロファイルで実行。IX+1、IY-1、2/3バイト、全5ペア、アドレス元との重複、FLAGS、位相差、CPU停止、WAIT、/RUNなし、拡張なし、故障時のADDR/EXP/ACTを確認。診断注入無効のCPUでも同じCOMを1条件実行。
- 内部単体試験は4サフィックス×IX/IY×5ペア×読書きの80命令ケース。-128/-1/0/+1/+127、長い03FFFF→040000の進行、短いFFFF→0000の折返し、上位値、8種類のF値、SPL保持を確認。通常、WAIT/停止、低速条件、故障注入、EI直後IM1、変位取得中に要求したNMIの6条件を実行。Z80モードで明示幅を使うIM1/NMI条件は各80回の受付と復帰後の値を確認。
- ネイティブADLでも、IM1/NMI×通常/WAIT・停止/低速の6条件で各40命令を実行。変位取得中に要求し、全バイト終了後の受付、24bit PCでの復帰、Fと転送値、SPS/SPLの保持を検証。MBASE=0Eで短い転送を含めます。各条件で割り込みフレームの実アドレス05007D～05007Fへの書込み120回／読出し120回も照合しています。
- MBASE=0EのADL試験に短いLDXを追加。40/52、IX/IY、5種類の変位について、0EFFFF→0E0000、アドレス元へのロード、上位03の保持、3バイト目と0F0000を破壊しないことを検証。
- LDHの6単体条件、EX(SP)共用、MEM/ALU/BLK/MUL/LEA/FETCH/制御/IRQ/NMI/MBASE/MADL/混在/TST、要求保持、実際のセカンダリスロットRTLを回帰確認。
- DOSがEIする診断条件を含め、DOS呼出しはZ80、MBASE0、拡張ゲート閉鎖、戻り直後DIの条件で実行。

単体試験の短いFFFFアクセスはフラットRAMモデルです。実機のFFFFはセカンダリスロットであり、既存実機COMでは短い転送に安全な予約低RAM領域を使用します。完全なMSX BIOS/DOS、ボード全体、配置配線後の遅延はシミュレーションしていません。

再実行入口は `python tools/verify_r17.py`。GHDL、Icarus Verilog、patchを使い、GHDL/IVERILOG/IVL_ROOT/VVPで環境を指定できます。結果はverification_result.json、個別結果はverification_groups、ログはverification_logsに収録。R16の比較CPUはdoc/r16_baseline、差分はdoc/R17_LDX.patch、再適用入口はtools/extend_ldx_r17.pyです。過去のdoc/toolsは履歴として残し、今回の入口は本READMEとRESTART_R17.md、verify_r17.pyを使用してください。

## 残る工程

| 項目 | R17時点 |
| --- | --- |
| 工程9のLDH/LDX | 実装・シミュレーション完了。R17の実機は未確認 |
| 命令別の実装監査 | 未実装・意図的除外・部分対応を命令一覧と照合する作業が残る |
| 工程7/8 | ネイティブADL IM0、MADL/混在RSTなどの残項目あり |
| 工程10 | GOWINタイミング収束、規模・配置配線確認、最終実機回帰が残る |

RUNALLの全PASSだけで、全eZ80命令・全動作条件の完成とは扱いません。次は命令別の監査と割り込み／混在の残項目を進めます。

## COM CRC32

| COM | bytes | CRC32 |
| --- | ---: | --- |
| EZ80LDX.COM | 21810 | CF2B63CE |
| EZ80LDH.COM | 10981 | 0FDF3B53 |
| EZ80CT1.COM | 23697 | EE98260C |
| EZ80D3.COM | 18896 | 14B01ADC |
| EZ80TST.COM | 12968 | 08ADDC8B |
| EZ80MEM.COM | 2268 | 0C7D91D6 |
