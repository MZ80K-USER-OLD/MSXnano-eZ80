# v9: 実行時モード遷移と02h/03hフレーム復帰の基盤

## 実装
ENABLE_MIXED=true、FETCH24=trueの場合に限り、ADL_Stateによる実行時モード遷移を追加。
RESET_ADL=falseが短い開始モード。RESET_ADL=trueで長い開始モード。
ENABLE_MIXED=false（標準）では従来v8と同じ固定開発モードを維持。
MSXトップ／プロジェクトはデフォルトFETCH24=false、ENABLE_MIXED=falseのまま。

今回対応した流れ:
- 短いモードで52 CD ll mm hhを取得し、戻りPC中位・下位・02hをSPLへ保存。
- CALL成功時ADL_State=1、24bitターゲットへ遷移。
- 長いモードの5B CALLは戻りPC上位・中位・下位・03hをSPLへ保存。
- 5B RETはモード情報を先に読み、03hなら3バイトPCと長いモードを復元。
- 02hなら2バイトPCをbank0へ復元し、短いモードに戻る。
- PCの順次／相対加算は状態に応じ16bit/24bit折返し。
- 5B JPの対応経路も長いモードへの遷移を行う。

短いモードのMBASEはまだ0固定。SPSとSPLは独立。
マーカー取込後にRETのオペランド数を選択し、不要な上位PC読出しを防ぐ。
02h/03h以外のマーカーはシミュレーションassertionで検出（合成除外）。

## 検証
GHDL 251実行PASS: v8回帰155 + mixed試験96。
新規sim/tb_mixed24.vhd: 8条件×成立/不成立×WAIT有/無×SPL3初期値。
短い開始→52 CALL→長い側の条件CALL/RET→03hで長い側に戻る→02hで短い側に戻る。
この流れを再CALLでも確認し、18回の書込み、02h/03h、各戻りアドレス、
SPL再使用、短いSP、上下ガード、bank0復帰、意図しない読出し範囲を検査。
SPLの030000→02FFFF、000000→FFFFFF、FF0000→FEFFFFを含む。
クロックenable1/16、位相分離捕捉。元T80/G80Aの8ファイルのSHA256は一致。
ログtest_results_v9.log。テストプログラムはVHDLテストベンチ内に含まれる。

## 限界
ADL_Stateは今回のフェッチ／対応分岐／フレーム選択の状態で、全命令ADL対応ではない。
ADL中でも無suffixの一般的なLD/CALL/RETは24bit仕様へまだ切替えていない。
テストでは長い命令を明示した5Bと、対応する52 CALLを使用する。
52の全命令適用、40/49を含む一般的な幅制御、非法suffixの検出、MBASE、
短長の分割スタックCALL、長いPUSH/POP、24bitデータアクセスは未実装。
5B CALLを短いモードで使うなど、対応範囲外の組合せは使用しない。
高位バンクIRQ/NMI、RETI/RETNも未対応。試験では割込みを禁止。
MSX側のA24メモリ接続は未実装で、新機能の実機試験はまだ不可。
v9のGowin合成・実機動作は未確認。既存COMは旧機能の回帰用。

## 残りの大きな段階
1. 命令幅制御の仕上げ: 通常ADL命令、短長suffix、必要なスタック命令。
2. 24bitデータアクセス: レジスタ間接、絶対アドレスなど。
3. MSXメモリ接続と実機ASM/COM: バンク割当、VDP優先とCPU WAIT。
4. 割込み復帰と総合検証: IRQ/NMI、RETI/RETN、命令回帰・実機確認。

これはMSX上で24bitプログラムを実行する目標の工程区分。
全eZ80命令の網羅的互換性までは追加工程が必要。版数は不具合や分割で増える。

参照: Zilog eZ80 CPU User Manual UM007715-0415、CALL/RETのMemory Mode Switching表。
https://www.zilog.com/docs/UM0077.pdf
