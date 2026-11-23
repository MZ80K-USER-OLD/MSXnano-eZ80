# R24.5：通常版／UART診断版の切り替え

## 使用するプロジェクト

| 版 | GOWINプロジェクト | UART監視ログ |
|---|---|---|
| 通常版 | fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj | 無効、TXはHigh固定 |
| UART診断版 | fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj | 元の監視・ログ生成回路を有効 |

基準はLogic 95%の実機確認済みレジスタ選択共通化版。
97%のFF版、96%のR24.4選択コード比較版からは作成していない。
CPU、トップ回路、VDP、メモリ、ピン・タイミング制約を含む既存FPGAソースは基準と同一。

2つのGPRJは、UARTデバッグモジュールの入力ファイル1本だけを選び分ける。

* 通常版：`fpga/src/msx2p_debug_disabled.v`
* UART診断版：`fpga/src/msx2p_debug.v`（基準と同じ実装）

どちらもモジュール名・ポートはmsx2p_debug。1つのプロジェクトへ両方を追加しないこと。
CPUやトップ回路を版ごとに複製したり、実行時のモード切り替え回路を追加したりしない。
切り替えはビルド時に行う。実機上でUART診断を有効化するには診断版ビットストリームを適用する。

## 通常版で残るもの

UART TXのトップポートとCST指定は維持し、アイドルのHighを出す。
UART監視回路からMSXへの制御出力はなく、boot_okは既存トップで未接続。
無効実装はboot_okを0へ固定するが、CPUやリセットに影響しない。
ログ送信ボタン用mono2も出力の有効な使用先がなくなるため、合成時の除去対象になる。

CPUの`.DIAGNOSTICS(EZ80_EXTENDED)`、eZ80診断I/O、メモリトレース、COMテストが使う機能は維持する。
通常版は「すべての診断回路を削除した版」ではなく、「UARTへ送る監視・ログ生成だけを無効化した版」。
SPS/SPL、ADL、幅プレフィクス、WAIT、割り込み、16bit MSX/24bit拡張バスとFFFF遮断は基準と同じ。
GSR利用は保留のまま。

## 設定とビルド

初めて開くプロジェクトでは、IDEの既定設定が基準と異なる可能性がある。
GPRJだけで全IDE設定を移植できたとは扱わない。
両版へ共通設定を適用するTclを同梱する。

### IDEのTclコンソールから開いて設定する

通常版：`source {展開先/fpga/configure_normal.tcl}`

UART診断版：`source {展開先/fpga/configure_diagnostic.tcl}`

このスクリプトは対象GPRJを開き、設定を適用する。合成は開始しない。
続けてIDEからビルドするか、`run all`を実行する。

### コマンドラインからビルドする

* 通常版：`gw_sh 展開先/fpga/build_normal.tcl`
* UART診断版：`gw_sh 展開先/fpga/build_diagnostic.tcl`

GOWINがPATHにない場合は、gw_sh.exeのフルパスで実行する。パスに空白がある場合は引用符で囲む。
スクリプトは自身の場所からGPRJを解決するため、実行ディレクトリに依存しない。
両版は別のプロジェクトフォルダでimplを生成し、出力の取り違えを防ぐ。

共通設定の主な値：

| 設定 | 値 |
|---|---|
| Top Module | top |
| Verilog | SystemVerilog 2017：sysv2017 |
| VHDL | VHDL 1993：vhd1993 |
| MSPI as GPIO | 1 |
| SSPI as GPIO | 1 |
| JTAG as GPIO | 0 |
| Place / Route Option | 0 / 0 |
| RAM R/W Check | 0 |
| Loop Limit / Max Fanout | 2000 / 1000 |

共通Tclのinclude_pathは実在するfpga/srcを指定し、既存print.vを参照する。
Dual-Purpose Pinと言語設定は、ユーザー提供の95%版の設定および公式Tcl資料を参照した。
GOWIN実行はこの環境では未確認で、スクリプトのTcl構文・引数・対象ファイル解決はモックで検証した。
手動で設定する場合も両版で同じ条件にする。タイミング制約の緩和は追加していない。

Tcl資料：https://cdn.gowinsemi.com.cn/SUG1220E.pdf

## リソース見込み

基準の配置配線結果はLogic 19,693、LUT 17,452、Register 7,447、RAM16 59、BSRAM 43。
UARTデバッグ階層はLUT 2,291、ALU 290、Register 678、BSRAM 1。
送信ボタン用mono2はLUT 11、ALU 23、Register 26。

単純差し引きではLogicが95%から83%前後へ下がる余地がある。
これは見積もりであり、全体最適化・配置配線によって変わる。通常版の実測値ではない。
診断版も、ファイルの場所やツール設定の影響を含め、95%へ完全一致する保証はしない。
両版ともGOWINで実数・FF・RAM・最悪Setup/Holdを確認すること。
基準版自体にもタイミング違反が残っている。

## 検証範囲

`python3 tools/verify_release_r24_5.py`

* 両GPRJの123ファイル参照が解決し、デバッグ実装1本だけが異なることを確認。
* 既存FPGAソースは通常版GPRJ以外すべて基準と同一で、CPU・トップ・メモリ・制約の変更がないことをSHA256で確認。
* 通常版はリセット・バス・send入力の活動中もTXがHighであることを確認。
* 診断版は既存の文字生成・UART送信を使い、実際のボーレート分周を維持して最初の6文字`state=`を復号。
* ログ開始までの100msスケジューラだけをシミュレーションで加速する。
* Icarus未対応のstreaming concatenationは、検証専用print.vコピーで1024bit入力のMSB側配置と右側ゼロ埋めを明示する。製品RTLは変更しない。
* 選択した全Verilogのプリプロセスと、トップ＋選択したlogger＋UARTの構文を確認。
* GOWINの命令をモックに置き換え、Tclの対象プロジェクト・言語・Dual-Purpose Pin設定を確認。

既存SD/HDMI RTLにはIcarusで完全に解析できない記述があるため、全基板回路のIcarusエラボレーション・BIOS起動を実施したとは扱わない。
CPUの再回帰は今回のUARTモジュール切り替えの論理検証では再実行せず、基準と同一であることを確認する。
配置配線後はファンアウトや配線も変わるため、実機回帰は必要。

## 実機テスト

COM 34本とRUNALL.BATは基準と同一。新しいテストプログラムをFLASHへ追加する必要はない。
両版とも同じテストを使用できる。

1. EZ80MEM /RUN
2. EZ80MR4 /RUN
3. EZ80LDH /RUN
4. EZ80LDX /RUN
5. RUNALL.BAT
6. SOFARUNからスペースマンボウの起動・PLAY

UART診断版では従来の送信ボタン操作とUARTログも確認する。
通常版ではUARTログが出ないのが意図した動作。

## デバッグ機能の由来

Goa'uldにもmsx2p_debug、print、UART送信器があり、MSXnanoだけで新規に作られた機能ではない。
RetroSiliconのstandalone版では監視項目・カウンタが拡張された実装が使われている。
現在の基準ソースはそのRetroSilicon版と改行形式を除いて一致する。
詳細は `doc/R24_5_UART_PROVENANCE.md` を参照。
