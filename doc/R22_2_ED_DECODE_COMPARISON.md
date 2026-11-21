# R22.2 — 反復I/OデコードをEDページ内へ移した回帰比較版

R22の実機報告を受け、反復I/Oの機能を維持したままデコードの置き方だけを変更した比較版。
**R22.2のGOWIN合成・実機確認・面積・Setup/Holdは未確認。実機原因の特定や修正完了を意味しない。**

## 報告された不具合

| 試験 | 実機報告 |
| --- | --- |
| EZ80IOR /RUN | CASE 0でフリーズ。PASS表示には到達しない |
| RUNALL.BAT | FAILあり。全失敗テスト名・詳細は未取得 |
| EZ80IR0 /RUN（INI2RをNOP×2に置換） | Stage 0、ADDR=0EFFFF、EXP=C3、ACT=7E |
| EZ80MEM /RUN | Stage 1、報告文字列ADDR=07FFE、EXP=31、ACT=7E |

MEMのユーザー入力アドレスは5桁の07FFE。配布COMのStage 1で最初に確認するアドレスは07FFFEであり、報告値の桁落ちかは未確認。報告文字列と試験設計値を区別する。
IR0は新規反復I/Oを実行する前のRAM初期化・読み戻しで失敗した。従ってINI2Rの反復処理だけに原因を限定しない。
7Eは診断のLD A,(HL)命令バイトと同じ値。ただし命令データ残留と確定しない。書込先、読出要求、SDRAM応答、CPU入力保持を区別する必要がある。

## 過去の実機回復例

R15.3では、TSTの主デコード末尾の一括上書きをやめ、ED opcode case内へ配置した。
その後のユーザー実機確認はCT1、D3、TST、MEMがPASS、RUNALLは当時未実装のLDH/LDX以外PASS、SofaRunからスペースマンボウPLAY。
記録は `R15_3_HARDWARE_BASELINE.json`、変更は `R15_3_TST_DECODE.patch`。
デコード配置変更と実機回復の前例であり、当時の厳密な物理原因まで証明した記録ではない。

R21.1にも全命令用のopcode変換MUXを取り除いた変更があるが、その直後にもメモリ不良は続いた。R15.3の実機回復例と混同しない。

## 今回の変更

変更したFPGAファイルは **fpga/G80A_eZ80/t80_mcode_ez80.vhd の1本だけ**。
R22では全命令ページのcaseの後に `if Block_IO_Repeat then ...` を追加し、MCycles/TStates/Set_Addr_To/IORQ/Legacy_Write/IncDec_16/NoRead/I_BTR等を上書きしていた。
これはR15.3で取り除いた構造と同様の末尾上書きで、R22で再導入していた。

R22.2では8命令の専用行をED opcode case内へ配置。末尾の反復I/O上書きは撤去した。対象opcodeを既存のED未定義NOP一覧から外し、EDC3はR800残存NOP行からも外す。拡張ロック時の無操作を維持する。

| 項目 | R22.2での扱い |
| --- | --- |
| 8命令の反復・BC/DE/HL更新・幅・フラグ | 同じ制御スケジュールを維持 |
| 既存ALU・レジスタ増減・上位byte共通書込 | 変更なし |
| CPU本体・幅prefix受付・レジスタファイル | 変更なし |
| ラッパ要求アドレス・データ保持 | 変更なし |
| MSX16bit／拡張24bitバス分離、FFFF遮断 | 変更なし |
| メモリブリッジ・SDRAM制御・TOP・診断記録 | 変更なし |
| GPRJ、DualPin、言語設定、CST、SDC | 変更なし |
| 既存COMと小型診断COM | byte単位で変更なし |

この変更によって合成後の段数・配線・面積が必ず改善するとは断定しない。GOWIN実レポートで確認する。一律multicycle/false_pathは追加しない。

## シミュレーション検証

- R22とR22.2のデコーダの全出力を比較。Mode0〜3それぞれ458752組、合計1835008組で一致。
- IR全256、ISet全4、Mサイクル1〜7、64個の設定パターンを走査。設定パターンは幅/拡張/割込み/XY/フラグ等を含むが、それぞれ独立の全直積ではない。無限の命令列・タイミングの形式的証明ではない。
- 新規反復I/Oと既存IO2の幅、WAIT・CE停止、反復途中のIRQ/NMIを回帰。
- EZ80MEM、D3、CTL、MR4、小型診断IR0/IR1/IR3、EZ80IORの実COMを接続したSDRAMモデルで実行。
- DOS内部がEIするスタブを使用。実MSX-DOS全体やゲームのシミュレーションではない。
- 検証の正確な件数・各ログはverification_r22_2に同梱。

## 実機での比較手順

1. 元のR22のimpl・レポート・ビットストリームを別に保管する。
2. このZIPを新しいフォルダへ展開し、`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`をGOWINで再合成・配置配線する。比較では元R22とTiming/Area等の設定をそろえる。
3. 新しく生成したビットストリームを適用し、電源を入れ直して最初に`EZ80MEM /RUN`を実行する。
4. `EZ80IR0 /RUN`でRAM_OK/CODE_OK/ENTER_TEST/RETURN_OK/PASSまで到達するか確認する。
5. MEMが再びFAILなら、既存の`EZ80MR4 /RUN`も実行し、CPU読出値とW/R記録の行を保存する。必要なCOMは同梱。
6. MEM/IR0がPASSなら、`EZ80IOR /RUN`、`RUNALL.BAT`、最後にSOFARUNからスペースマンボウの起動・PLAYを確認する。

COMは変更していないので、EZ80IORの期待表示は従来どおり `EZ80IOR R22: PASS`、IR0は `EZ80IR0 R22.1: PASS`。FPGAの比較版番号R22.2とは別。
まだ失敗する場合は、最初のFAILのテスト名、Stage、6桁のADDR、EXP/ACTと、GOWINのimpl ZIPが次の切り分け資料になる。

実機でMEM等が回復しても、同一の論理から合成・配置配線が変化した影響と厳密な捕捉タイミングの照合を続ける。これだけでSTA収束や全eZ80互換の完成を宣言しない。
