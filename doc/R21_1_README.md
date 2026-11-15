# R21.1 — R21のメモリFAILを調べる比較修正版

R21実機のEZ80MEM最初のFAIL（07FFFE / EXP31 / ACT7E）とEZ80IO2 CASE 0停止に対応。
**原因は未確定です。R21.1はGOWIN/実機未確認です。**

## 変更

- 全デコードの入口にあったIO2用opcode読替えMUXを削除。
- EDページのINI/IND/OUTI/OUTD行に4つのopcodeを直接追加し、既存転送回路・ALUを共用。
- 拡張無効時は従来どおり未定義NOPを維持。
- 診断読出しprocessの感度リストにDiag_Activeを追加。
- R21比のFPGA変更はt80_mcode_ez80.vhdとg80a_ez80.vhdの2ファイル。
- MSX16/拡張24アドレス分離、要求保持、SDRAM回路、top、GPRJ、SDCはR21と同一。
- SLP非対応NOP、TRAP非対応の方針を維持。

詳細はdoc/R21_IMPL_ANALYSIS.mdを参照。

## ビルドと実機確認

1. 別フォルダへ展開し、fpga/project_eZ80/MSXNanoTang20K_eZ80.gprjを開く。
2. 古いimpl/bitstreamを流用せず、R21.1のプロジェクトで再合成・配置配線して書き込む。
3. 電源投入後、まずEZ80MEM /RUN。期待表示はEZ80MEM P1: PASS。
4. PASSしたらEZ80IO2 /RUN。CASE 0〜15の後、EZ80IO2 R21: PASSが正常。
5. 続いてRUNALL.BATとSOFARUNからスペースマンボウの起動・PLAY。
6. Logic使用率とR21.1のimpl ZIPを報告。

EZ80MEMがFAILなら、表示を記録し、新IO2試験よりメモリ経路の調査を優先する。
FAIL/停止時は電源再投入してから次の試験を行う。

## テストファイル

**COMの更新はありません。既に書いたR21用テストをそのまま使えます。**
同梱hardware_testの30本とRUNALL.BATはR21配布版とバイト一致。
- EZ80MEM.COM: 2268バイト、CRC32 0C7D91D6。
- EZ80IO2.COM: 22162バイト、CRC32 5E92DDA4。
テスト名の表示はR21のまま。R21.1という表示には変更していない。
既配布のEZ80IP0〜IP3診断も同じ機能識別値を使用するため適用可能。

## ローカル検証

- 新IO2の244条件＋新COMの7プロファイル＋既存61プロファイル、計312条件/プロファイル。
- GHDLのVHDL-93解析（6ファイル）。
- 旧R21とR21.1のマイクロコード全出力を1,835,008入力条件で比較。
  opcode256 × page4 × Mcycle7 × control64 × Mode4。
  各入力で実際のClassify_Write(opcode)を使用。2値入力の選択した組合せであり、形式的な全状態等価証明ではない。
- 配置配線の遅延、メタステーブル、アナログSDRAM条件、実機不具合を再現した試験ではない。
- GOWINでのLUT/段数/STA改善は未測定。実機修復も未確認。

旧doc/R21_README.mdやROADMAP中のR21情報は過去版の記録。本版の状況はこのREADMEとverification_r21_1/summary.jsonを参照。
