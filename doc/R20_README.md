# R20 — CPUローカルSLP

実機確認済みのR19.1を基準に、拡張をアンロックした場合のSLP（ED 76）を追加しました。CPUは既存のクロックイネーブルを止めて保持し、外部バスをアイドルにします。SDRAM、VDP、音源、システムクロックは止めません。R20のGOWIN合成・配置配線・使用率・タイミング・実機は未確認です。

## 基準となるR19.1の実機結果

ユーザー確認済み：EZ80PFX R19.1:PASS、EZ80MEM P1:PASS、EZ80RW2 R18.2:PASS、EZ80IM0 R19:PASS、EZ80RS8 R18:PASS、RUNALL.BAT全項目PASS。SofaRunからスペースマンボウを起動・PLAY成功。

Logic94%、LUT/ALU/ROM16合計19059（LUT17182、ALU1877、ROM16=0）。R19比LUT+59です。この使用率はR19.1の値で、R20の測定値ではありません。

## 採用したSLP仕様

| 条件 | 動作 |
|---|---|
| 拡張ロック中、またはDATA_EXTENDED=false | ED76を従来Z80のIM1別名として維持 |
| アンロック後のZ80/ADL | ED76完了後、CPUローカルのSLP状態へ移る |
| 停止中 | PC・レジスタ・フラグ・割り込み許可状態・IMを保持。新しいフェッチ、メモリ/I/O要求、CPUリフレッシュは発行しない。HALT_n=0 |
| IRQ/NMI/WAIT/BUSRQ | 通常SLPの解除には使わない。停止中はBUSAKを新規に返さない |
| 外部RESET | SLPを解除し、CPU全体をリセット。Z80互換・拡張ロック状態から再起動 |
| 診断窓のD3を事前にアーム | テスト専用。SLPに入った後、既存カウンタで待ち、CPUリセットなしで解除 |

R20では、SLP完了直前のIRQ/NMI要求がある場合もSLP成立を優先し、割り込みフレームは作りません。これは今回採用したCPUローカルSLPの動作条件です。

SLP完了前のWAITは既存バスサイクルを延長します。BUSRQでバスを明け渡している間はSLPへ入らず、バスが戻った命令境界で入ります。停止中にCPUが発行するリフレッシュはなくなりますが、基板側SDRAMコントローラのクロックと既存の更新処理は変更しません。

注意：現行SDRAMコントローラのリフレッシュ選択はCPUの `bus_rfsh_n` に依存します（`fpga/src/memory_ez80.v`）。R20はSLP中にCPUリフレッシュを発行しないため、長時間SLP中のSDRAM/VRAMデータ保持と画面維持は保証しません。通常SLPはリセット再起動を前提とします。短時間の診断解除試験を、長時間のメモリ保持試験とは扱いません。自律リフレッシュや自己リフレッシュへの移行は今回追加していません。

CPUマニュアルはSLPの詳細を製品仕様へ委ねています。参照したeZ80L92のSLEEPはリセット復帰方式です。R20はこの復帰条件を採用したFPGA向けCPUローカル実装で、eZ80L92の発振器停止・RTC・WDT・全周辺回路の省電力動作を再現するものではありません。IRQ/NMIで通常復帰する独自SLPとしては実装していません。

HALT命令は従来どおりです。SLPをHALTへの別名にせず、SLP専用の保持ビットを1個追加しています。データレジスタ、フレーム処理、演算器、FSM状態は増設しません。診断待ち時間は既存Diag_NMI_CountとアームFF、完了記録は既存Diag_Selectを共用します。実際のLUT/FF増減はGOWINで測定してください。

## 実機用テスト

```text
EZ80SLP /RUN
```

期待表示：`EZ80SLP R20: PASS`

`hardware_test/EZ80SLP.COM` とプロジェクト直下に収録。22936バイト、CRC32 `17B1337E`。旧COM28本はバイト単位で変更せず、新規1本を加えた29本をテストZIPへ収録します。既存RUNALL.BATはそのままです。

20ケース：Z80/ADL × MADL=0/1 × プレフィクスなし/.SIS/.LIS/.SIL/.LIL。MADL=1のケースは、診断IRQを保留してEI直後にSLPを実行します。診断解除後は直ちにDIし、AF、SPS/SPL、SLP完了記録A7を検査します。単に次命令へ進むNOPでは完了記録が付かず、PASSしません。最初の失敗はStage・ADDR・EXP・ACTを表示します。

**このCOMは診断専用解除を使ってDOSへ帰ります。通常SLPのリセット復帰を実機で検査したという意味ではありません。** リセット復帰、IRQ/NMIによる解除なし、停止中のバス・レジスタ保持はCPU単体試験で確認します。実機で通常SLPを直接実行すると、リセットまで戻りません。

私有コード/結果は0A:6000/7000/8000/8100および0E:8200、SPLは05:0001近傍です。SPS=C001を保持し、SPLの私有領域でAFを保存・復元します。MSX/DOSの低位ベクタ、MegaRAM/VRAM予約枠は書き換えません。

/RUNなしはREADY、旧版R19.1以前や診断無効はNOT READY、拡張無効はUNSUPPORTEDで停止試験へ進みません。

DOS/BIOSがEIする条件を考慮し、私有試験中にはシステムコールを行いません。終了時はDI、Z80/MBASE=0、MADL=0、元のDOSスタック、IM1、診断終了・拡張ロックを復元します。DOS表示の後もDIをやり直してIX/IYを復元し、EIして終了します。シミュレーションのDOSスタブ内部でもEIし、DOS側IM1の受付・復帰を確認します。

## ビルドと実機での確認順

新しいフォルダへ展開し、同じ `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を使います。

1. GOWINで合成・配置配線。Logic、LUT/ALU/FF、CLS、Setup/Holdの結果を記録。
2. `EZ80MEM /RUN`、`EZ80RW2 /RUN`。
3. `EZ80SLP /RUN`、`EZ80PFX /RUN`、`EZ80IM0 /RUN`、`EZ80RS8 /RUN`。
4. `RUNALL.BAT` を実行。
5. SofaRunからスペースマンボウを起動してPLAY。

古いimpl/bitstreamは含めません。DualPin、SystemVerilog設定、GPRJ、CST、SDC、メモリ配置、16bit MSXバスと24bit拡張バスの分離はR19.1から変更しません。新しいfalse path、multicycle、max-delay指定はありません。今回の実機PASSはSTA収束の代わりにはなりません。

## 診断識別とテスト解除

既存C4〜CDの機能識別を維持。CE=01/CF=FEがR20のSLP識別です。DIAGNOSTICS=trueかつD8窓が有効な場合だけD3を受け付け、既存のNMIアーム/カウンタをテスト待ち時間として使います。このD3中には診断NMIを出しません。

D3選択時の読み出しは53（アーム済み）。SLP状態でカウンタが最後まで進むと、Sleep_Test_Releaseを1回成立させ、既存の選択レジスタをD5へ移します。D5読み出しA7が完了記録です。D5の完了値をI/O書き込みだけで設定するコマンドはありません。D4は保留IRQ等の解除、D0は診断窓終了です。診断無効時にはテスト解除入力が0に固定されます。

## 検証と限界

`verification_r20/summary.json` に結果を集約します。

- SLP単体244ケース。4アンロック状態（Z80/ADL×MADL）、5幅、直前のIRQ/NMI/同時要求/要求なし、通常/WAIT・CEN停止を組み合わせます。停止後もIRQ/NMI、WAIT、BUSRQを加え、PC・SPS/SPL・AF・I/R・IM・ADL/MADL/MBASE・IEF・MCycle/TStateとバスが保持されることを確認。追加80ケースではSLP完了直前にBUSRQでバスを明け渡し、返却時にSLPへ入ることを確認。PCの64KiB境界、RESETでのロック状態への復帰も検査します。
- ロック中とDATA_EXTENDED=falseのED76はIM1別名を維持。誤ったPC期待値を故障注入し、検査がFAILすることも確認。
- 実際のCOMをCPU＋ブリッジ＋SDRAMモデルで実行。通常、ストレス、故障検出、READY/UNSUPPORTED/NOT READYを検査。実際に20回SLPへ入り、停止中のバスが非活動であることと診断待ち時間も監視します。
- R19.1のプレフィクス、IM0、RST、混在CALL/RET、IRQ、メモリ、ロック状態の回帰とVHDL-93構文解析。

全MSX-DOS/BIOSの再現、全ISA認証、物理的な電力低減の測定、GOWIN実行、実機PASS、タイミング収束を示すものではありません。リセットのみで復帰するSLPの実機試験と、診断解除を使うCOM試験を区別してください。

## 次の残項目

混在制御命令の一部幅指定、追加I/O群の命令別監査、非法命令TRAP、全命令の独立照合、最終タイミング・規模・実機検証が残ります。ポート上位8bitを00固定する追加I/Oを実装しない方針は維持します。

一次資料：

- [Zilog eZ80 CPU User Manual UM007712](https://media.digikey.com/pdf/Data%20Sheets/ZiLOG%20PDFs/eZ80%C2%AE%20CPU%20User%20Manual.pdf)、p415 SLP：詳細は個別製品仕様を参照、フラグ変更なし、ED76。
- [Zilog eZ80L92 Product Specification PS013010](https://docs.rs-online.com/66b7/0900766b80387bea.pdf)、p35–36 SLEEP/HALT：SLEEPのリセット復帰条件とHALTの割り込み復帰条件。

2015年版UM007715の一覧ではSLPはp347です。今回、公式配信先のリダイレクトにより同ページ本文を直接取得できなかったため、取得できたZilog発行の2003年版本文と製品仕様を根拠にし、2015年版本文を確認したとは扱っていません。
