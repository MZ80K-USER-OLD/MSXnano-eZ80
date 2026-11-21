# R22.3: WAIT停止診断版

R22.2ベースの観測専用版。原因修正・GOWIN合成・実機確認はまだ行っていません。

ビルド対象: `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

実機で `hardware_test/EZ80MR5.COM /RUN` を実行します。停止後のLEDを撮影し、S2を1回押して1秒待つ操作を3回繰り返し、計4枚を取得してください。S1リセットは記録を消します。

詳細: [doc/R22_3_WAIT_DIAGNOSTIC.md](doc/R22_3_WAIT_DIAGNOSTIC.md)

以下は従来版の説明です。

# R22.2 — ED内デコード統合・回帰比較版

R22実機でEZ80IOR CASE 0停止、IR0とMEMの読戻しACT=7E、RUNALLにもFAILという報告を受けた比較版です。
変更したFPGAソースは **t80_mcode_ez80.vhd 1本だけ**。末尾の反復I/O制御上書きを撤去し、8命令の処理をED命令case内へ移しました。機能・命令スケジュールはR22と同じです。

**GOWIN合成・実機回復・Logic使用率・タイミングは未確認。原因特定済みの版ではありません。**
R15.3のTSTデコード統合後に実機回帰が回復した前例を踏まえた変更です。

GOWINは `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`。新しいフォルダで再ビルドし、新しいビットストリームで比較してください。

最初は `EZ80MEM /RUN`、続いて `EZ80IR0 /RUN`。PASSなら `EZ80IOR /RUN`、`RUNALL.BAT`、SOFARUNでゲームを確認。
MEMがFAILなら `EZ80MR4 /RUN` のW/R記録も比較材料になります。
COMは変更していません。EZ80IORの表示版はR22、IR0はR22.1のままです。小型診断IR0/IR1/IR3も同梱。

- [変更・過去の実機回復例・確認手順](doc/R22_2_ED_DECODE_COMPARISON.md)
- [命令機能一覧（R22と同じ）](doc/EZ80_INSTRUCTION_STATUS_R22.md)
- [残る工程](doc/REMAINING_R22.md)
- 検証ログ: verification_r22_2

以下は旧版の履歴です。

---

# R22 — 反復ブロックI/O追加

R21.3実機確認済み版を基準に、INI2R/IND2R/OTI2R/OTD2R/INIRX/INDRX/OTIRX/OTDRXを追加。
**R22のGOWIN合成・実機・Logic使用率は未確認。** SDC等の制約変更なし。

GOWIN: `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

実機の新規テスト: `EZ80IOR /RUN` → `EZ80IOR R22: PASS`。COMはルートとhardware_testに同一ファイル。RUNALLに追加済み。
続いて `EZ80MEM /RUN`、`EZ80IO2 /RUN`、`RUNALL.BAT`、SOFARUNでスペースマンボウの起動・PLAYを確認。
新規COMは32ケースでCASE 0〜31を表示。CRC32: `643ACD66`（53097 bytes）。旧FPGAではNOT READY。

- [R22実装・テスト説明](doc/R22_BLOCK_IO_REPEAT.md)
- [命令実装一覧](doc/EZ80_INSTRUCTION_STATUS_R22.md)
- [残る工程](doc/REMAINING_R22.md)
- [R21.3のデコード説明](doc/EZ80_DECODE_IMPLEMENTATION_R21_3.md)
- [R21.3の最悪Setup経路](doc/EZ80_WORST_SETUP_PATH_R21_3.md)（R22再測定値ではない）

以下は旧版の履歴資料。

---

# R21.3 — 最新資料更新

実機: MEM/IO2/MR4/RUNALL全PASS、SOFARUNからスペースマンボウ起動・PLAY確認。Logic94%。Setup/Holdは未達。

[doc資料一覧](doc/README.md)に命令97ニーモニックの実装状況、デコード実装、最悪Setup経路、残り工程を追加。RTL/COM/制約の変更はなく、再ビルド不要。

以下は配布時の説明。当時の未確認という記述より、上の最新確認結果を優先する。

# R21.3 — 観測接続の修正・比較版

## 基準と未解決事項

R21.2はユーザー実機でEZ80MEM、EZ80IO2、RUNALL全項目がPASS、SOFARUNからスペースマンボウ起動・PLAYを確認済み。
一方、MR3は全6試験のCPU値とHLが一致するものの、W/R記録がすべてゼロのためFAIL。
R21.2 implはLogic 19857/20736 (96%)、LUT 17626、ALU 1877、Register 7362/15915 (47%)。
54MHz系報告Fmax=25.191MHzで、STA未達は残る。
以前のメモリ不具合が消えた原因は未確定。R21.2の機能PASSをSTA合格と扱わない。

R21.3のGOWIN・実機・リソース・タイミングは未確認。

## 変更

- 64bitの記録をVHDL内の可変スライスで選択する構成をやめる。
- Verilog側のez80_trace_mux.vで、定数範囲のcaseを使って8bitを選択する。
- ラッパから4bitのTrace_Selectを出し、8bitのTrace_Dataを明示接続。入力の初期値指定も除去。
- FD/FEで、同じ8bit接続を通す55H/AAHを読み出せるようにする。
- 識別FB/FCは03/FC。新しいEZ80MR4.COMを使用。
- GPRJへez80_trace_mux.vを追加。

これは合成・言語境界を切り分けるための構造変更。GOWINの不具合、可変スライス又は入力初期値が原因と証明したものではない。
R21.2比でCPU本体、マイクロコード、ALU、レジスタ、パッケージ、ブリッジ、SDRAM制御、CST、SDCは同一。
CPUの新命令実装は増やさない。SLP非対応NOP・TRAP非対応も維持。
観測byte選択は1個を共用。読出し記録は既存ram_addr/resultを共用。R21.2の31bit書込み記録を維持し、RTL上の追加FFはない。
合成後に記録FFが残るようになる場合を含め、GOWINでのLUT/FF増減は未測定。

## 実行手順

1. 別フォルダへ展開し、fpga/project_eZ80/MSXNanoTang20K_eZ80.gprjで再ビルド。
2. 新しいbitstreamを書き込み、同梱EZ80MR4.COMをDOSドライブへコピー。
3. 電源再投入後、`EZ80MR4 /RUN`を単独実行。
4. LINK行、A/I・HL・W/R行、最終結果を報告。画面写真でよい。
5. `EZ80MEM /RUN`と`EZ80IO2 /RUN`も確認。Logic使用率とimpl ZIPも保存。

**FPGAの再ビルドが必要。以前のMR3ではなくMR4を使う。**
旧bitstreamでは新MR4はNOT READYとなる。R21.3で旧MR3を実行しても識別変更によりNOT READYとなる。
既存の通常テストCOM 30本とRUNALLは更新なし。MR3もファイル内容は維持するが、本版の診断には使わない。
MR4はhardware_testとルートの両方に同じCOMを同梱。RUNALLには追加しない。

正常表示:
```
EZ80MR4 R21.3 START
LOCAL EXP=31 ACT=31
LINK EXP=55/AA ACT=55/AA
...
A 07FFFE E31 A1=31 A2=31
I1=31 I2=31 HL=07FFFE
W=6BFFFE/31 R=6BFFFE/31
...
EZ80MR4 R21.3: PASS
```

- LINKが違う: TRACE LINK FAILで、拡張RAM試験の前に終了。観測用の接続を先に調べる。
- LINKだけ一致しW/Rがゼロ: 同じ8bit接続の定数経路は通るが、記録値の経路が未確認。メモリ障害と混同しない。
- W/Rの物理アドレスやデータが違う: doc/R21_1_HARDWARE_ANALYSIS.mdの解釈を参照。
- LINKは接続の試験であり、全記録bit・保持FF・SDRAM書込み完了を独立に証明するものではない。

試験先は論理010100/070100/07FFFE、物理650100/6B0100/6BFFFE。
A行は絶対指定で31H、I行はHL経由でCEHを書き、両方式で2回ずつ読む。
Wは受理した書込みの物理アドレス/データ。Rは最後の読出し要求の物理アドレス/ブリッジ返答。
記録値を読む間に次の拡張要求を出さない。観測記録は履歴FIFOではない。

DOSがEIすることを前提に、呼出し前にZ80/MBASE0・拡張ロック、直後DI。SPS/IX/IYを復帰。
新IO2命令、ADLコードフェッチ、FFFFH境界試験はMR4では使わない。

## ローカル検証

MR4実COMの8プロファイル:
- 通常、CPU許可停止、人工的な20H故障注入、拡張無効、/RUNなし、旧版識別。
- 観測接続をゼロへ固定: LINK FAIL、拡張RAMアクセスなし。
- 接続の55/AAだけ正常で記録をゼロへ固定: CPU値は一致、記録不一致でFAIL。実機MR3と同じ表示上の区別を確認する人工条件。

既存EZ80MEM 9、既存EZ80IO2 7を合わせ24プロファイルが期待結果。
VHDL-93解析6ファイルと、top/ラッパ/ブリッジ/新muxの部分的な接続確認も実施。
MR4の接続異常条件は、WAITが発生しない正常な早期終了に合わせてテストベンチの期待条件を修正し再実行。他7条件の成功ログも保持。
故障注入、READY/NOT READY/UNSUPPORTED等の期待された終了を含む。24個の実機PASSではない。
GHDL変換CPU＋ブリッジ/SDRAM RTL＋SDRAMモデルによる検証であり、GOWINネットリスト・物理タイミング・実機不具合の再現ではない。

EZ80MR4.COM: 4108バイト、CRC32 86A79F3D。
本版の情報はこのREADMEとverification_r21_3/summary.jsonを参照。旧版の資料は履歴として同梱。
