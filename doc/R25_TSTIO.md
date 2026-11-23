# R25 TSTIO実装と検証範囲

## 仕様

Zilog eZ80 CPU User Manual UM007715-0415、p.367 TSTIO、p.77命令概要を参照。
公式資料URL：https://zilog.com/docs/UM0077.pdf

| 項目 | 実装 |
|---|---|
| opcode | ED 74 nn |
| アドレス | 0000h:C。I/Oの上位16bitを0にする |
| 演算 | 読み出したI/Oデータ AND 即値nn |
| S／Z／P/V | 結果の符号／ゼロ／偶数パリティ |
| H | 1 |
| N／C | 0 |
| A・汎用レジスタ・SPS／SPL | 維持 |
| Z80モード／ADLモード | 拡張有効時に対応。幅プレフィクス付きも1byte即値 |
| 拡張ロック時／他CPUモード | 元のED74 NEG別名を維持 |

TSTIOは今回指定された例外として、上位I/Oアドレスを0にする命令を実装する。IN0／OUT0等を追加する変更ではない。通常Z80のIN／OUTは16bitポートアドレスを維持する。

## 構成と捕捉タイミング

R24.5のRAM併用レジスタ、メモリブリッジ、SDRAM、VDP、UART通常／診断の選択、GPRJ、CST、SDCは維持する。GSR化、全FF化、バス統合、タイミング例外追加は行わない。

| 段階 | 動作 |
|---|---|
| ED74の取得 | EDページ・拡張有効・Mode0を条件にEC_TSTIOをIRと同時に保持 |
| M2 | 即値をメモリから取得し、PCを1進める。LDZで既存TmpAddrの下位8bitへ保持。次のアドレスを00:Cへ設定 |
| M3 | 既存IORQ経路で入力。BusAに保持済み即値、BusBに入力データを渡し、既存AND ALUでフラグだけ更新 |
| WAIT／CEN停止 | 既存の要求ラッチとCPU停止規則に従う。即値を入力データで上書きしない |
| IRQ／NMI | 命令完了境界で受付。即値取得とI/O入力の間で別命令へ遷移しない |

データ用の新しい作業レジスタは追加していない。既存TmpAddr.L、BusA／BusB、AND演算器、フラグ生成を共用する。exec_control_tを53bitから54bitへ拡張し、新しい制御保持bit EC_TSTIO=53を加えた。GOWIN最適化後のFF・LUT増減は未測定。

BusAの新しい選択コード1100をTmpAddr.Lへ割り当てた。既存POP AF等が使う1011には変更を入れていない。最上位バンクのI/Oゼロ化は既存ラッパーをそのまま使う。16bit MSXバスと24bit拡張バスの分離、$FFFFセカンダリスロット遮断も維持する。

## 実機用COM

`hardware_test/EZ80TIO.COM`、期待表示 `EZ80TIO R25: PASS`。

Z80／ADL × 無指定・40h・49h・52h・5Bhの10ケース。非ゼロ上位BCを設定してTSTIOを実行し、A／BC／DEと両SP、フラグを検査する。MBASE=0Ehのコードも経由する。

使用する00E6hは既存CPU診断ポートで、入力値は上位I/Oアドレス XOR 5Ah。正しいTSTIOなら上位00hなので5Ahとなる。BCのBは9Ahを設定するため、誤ってBC16を使うと異なるデータになり検出できる。診断セッション中だけ有効で、外部I/Oピンはラッパーが抑止する。実際の外部周辺機器からのデータは別のCPUピンシミュレーションで検証する。

診断ID E2h=25h／E3h=DAhを確認してから本体を実行する。旧機能ID・診断なし・拡張なし・/RUNなしの終了ガードを設ける。既存のE0h/E1h等のIDは変えない。

DOS表示はZ80・MBASE0・拡張ロック状態へ戻してから行い、システムコールがEIする前提で復帰直後にDIする。テスト中にMSXの割り込みベクタやセカンダリスロットを書き換えない。メモリ不一致時にはStage、ADDR、EXP、ACTを表示する。

## ローカル検証

- デコード524,288入力：既存53bit制御の全ビットがR24.5と一致し、新bitだけが対象ED74で有効になる。
- ピン側TSTIO：Z80／ADL、全4幅プレフィクス、複数ポート・マスク、CEN／WAIT／BUSRQ。I/O上位ゼロ、MREQ分離、フラグ、全GP・両SP維持、読出し回数を確認。
- 命令途中のIRQ／NMI：Z80／ADLの各20件。I/O前に受け付けず、RETI／RETN後にフラグとレジスタが一致することを確認。
- 拡張ロック時のED74 NEG：全A値256、ストレス有無で検査。
- 実COM：通常、CEN停止、故障注入、拡張なし、/RUNなし、旧機能ID、診断なし。DOS内EIと実際のIM1受付もモデル内で確認。
- MEM／D3／ALU／BLK／LEA／CTL／LDH／LDX、TST、DEC／PFX／IM0／IONの回帰。

具体的な合否と件数はR25_VALIDATION.jsonと各ログに記録する。これは全命令・全入力のCPU等価証明ではない。実eZ80のパイプラインやクロックサイクル数との一致も主張しない。

既存sim/build_tst_r15.pyのED74 NEG試験は、拡張ロック状態での試験へ更新した。拡張有効時のED74をNEGとする旧試験は、今回の仕様変更と矛盾するため使わない。

## 未確認

GOWIN合成・配置配線、LUT／FF使用量、Setup／Hold、実機でのTSTIO、既存ゲーム動作は未確認。R24.5基準の54MHzタイミング問題も解消していない。実外部I/Oデバイスの電気的タイミングと全組合せの最終ISA認証は残る。

## 再実行

GHDL 5.0.1とIcarus 11.0を使用。必要に応じてGHDL、IVERILOG、IVL_ROOT、VVPを環境変数で指定する。

```
python tools/synthesize_r25.py
python tools/verify_tstio_decode_r25.py
python tools/verify_tstio_r25.py
python tools/verify_tstio_com_r25.py
python tools/verify_regression_r25.py
python tools/verify_compat_coms_r25.py
```

COM再生成は `python hardware_test/build_tstio_r25.py`。既存COMを再生成する必要はない。
