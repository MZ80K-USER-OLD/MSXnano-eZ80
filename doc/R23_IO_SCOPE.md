# R23 — 追加I/Oを5命令へ限定

基準版はR22.4。ユーザー実機でMR6/MX6/MEM/RUNALL全PASS、SOFARUNからスペースマンボウ起動・PLAY、Logic96%を確認した版。
R22以前のメモリ不一致の物理的原因、配置配線後タイミングの収束は未確定。診断回路による配置変化の可能性を残す。

## 今回の範囲

| 命令 | opcode | ポート／カウンタ |
|---|---|---|
| INIRX | ED C2 | 固定DE[15:0]、BC回数、HL前進 |
| INDRX | ED CA | 固定DE[15:0]、BC回数、HL後退 |
| OTIRX | ED C3 | 固定DE[15:0]、BC回数、HL前進 |
| OTDRX | ED CB | 固定DE[15:0]、BC回数、HL後退 |
| TSTIO n | ED 74 n | 00:C[7:0]の入力とnをANDし、フラグ更新。Aは保持 |

RXのBC/HLはデータ幅に従って16/24bit。DEは全24bitを保持し、物理I/Oには下位16bitを使う。I/O時のA23:16は既存ラッパで0。
TSTIOは公式仕様に合わせA23:8=0とする。今回の明示指定により、この命令だけ従来の「追加I/Oで上位8bitを0固定するものは除外」の例外にする。
TSTIOのS/Z/PはAND結果、H=1、N=C=0。公式表にないX/Yは既存AND回路に従う。
即値nはZ80/ADL・全suffixで常に1byte。BC、DE、HL、A、メモリへ結果を書かない。

IN0/OUT0、INIM/INDM/OTIM/OTDMと反復版など、上記5命令以外のeZ80追加I/Oは対象外。
通常Z80のIN/OUT/INI/IND/OUTI/OUTD/INIR/INDR/OTIR/OTDRは維持。
SLPをNOPとする方針、未定義命令TRAPを実装しない方針も維持する。

## 削除した経路

- INI2/IND2/OUTI2/OUTD2（ED84/8C/A4/AC）の分類とB/Cを別々に更新するM4/M5を削除。
- INI2R/IND2R/OTI2R/OTD2R（ED94/9C/B4/BC）の分類とDEを進退させるM5分岐を削除。
- 除外した8opcodeはEDの既存NOP行へ置く。拡張有効時もI/O、反復、レジスタ更新を起こさない。
- 通常Z80ブロックI/O行からIO2専用の条件分岐を取り除く。従来T80の転送行を使用。
- RXは既存IncDec・上位byte書込みポート・BTR再フェッチと割込み境界処理を共用する。

内部の旧名Block_IO2は既存試験との接続名として残るが、判定はクラスDのRXだけ。単発IO2を実装している意味ではない。
Block_IO_Repeatはその同一信号の別名で、独立したFFやデコードを追加しない。
TSTIOは解放されたクラスCへ登録し、ED74の行で処理する。全命令ページの後段へopcode上書きMUXを追加しない。

## TSTIOの共用

M2で即値を既存TmpAddrの下位byteへ保存し、既存アドレス選択aBCでCを取り出して上位を0にする。
M3でI/O入力を読み、既存AND ALUとフラグ書込み経路を使う。BusAの選択肢にTmpAddr下位byteを追加する。
専用8bitマスクレジスタ、専用ALU、専用カウンタは追加しない。
拡張ロック中のED74は従来どおりNEG別名であり、即値byteをTSTIOとして消費しない。

CPU本体・パッケージ・mcode・ラッパの4ファイルを変更する。メモリブリッジ、SDRAMコントローラ、R22.4観測回路、16bit/24bitバス分離、top、GPRJ、CST、SDCはR22.4と同一。
GOWINでのLUT/Logic/CLS・Register増減は未測定。回路の共有・削除量を、そのまま配置後の削減率とは扱わない。

## 実機手順

1. 新規フォルダへ展開し、`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を合成・配置配線する。
2. この版で生成したイメージを書き込み、再起動する。
3. 新しい `EZ80IRX.COM`、`EZ80TIO.COM` と `RUNALL.BAT` を実機へコピーする。
4. `EZ80IRX /RUN` → `EZ80IRX R23: PASS` を確認する。
5. `EZ80TIO /RUN` → `EZ80TIO R23: PASS` を確認する。
6. `EZ80MR6 /RUN`、`EZ80MX6 /RUN`、`EZ80MEM /RUN`、更新したRUNALLを確認する。
7. SOFARUNからスペースマンボウの起動・PLAY、GOWINのLogic/CLS/Register使用量とタイミングを比較する。

新規COMは2本とも同梱し、従来COMのbytesは変更しない。RUNALLからEZ80IO2/EZ80IORを外し、IRX/TIOへ置き換える。
旧COMは履歴として残る。R23で旧IO2/IORを手動実行するとNOT READYになるのは機能識別変更に伴う意図した結果。
R23識別は既存E7E7診断窓のE0/E1セレクタで23/DC。旧IO2識別F8/F9は00/FF。
新しい物理I/Oポートは追加しない。

| ファイル | bytes | CRC32 |
|---|---:|---|
| EZ80IRX.COM | 26791 | 7EF14506 |
| EZ80TIO.COM | 23701 | 072C9C7C |

IRXはZ80/ADL、4命令、幅指定あり／なしの16ケース。内部ポートE6のループバックで検査する。
TIOはZ80モードで5prefix形×8マスクの40ケースと、除外8命令のNOPを検査する。00E6の入力5Aを使い、外部MSX IORQを抑止する。
両COMともMSX-DOS/BIOSがEIすることを想定し、表示はZ80・MBASE0・拡張ロック状態で行い、復帰直後にDIする。
メモリ比較のFAILはADDR/EXP/ACTを出力する。TIOのADDRは比較した通常MSX側の保存領域を示す場合がある。
内部ループバックは実周辺機器の電気的I/Oタイミングの検証ではない。

## 検証と残る確認

- RXの324ケース: Z80/ADL、5幅形、通常／WAIT／CE停止、IRQ/NMI、BCの16/24bit境界。
- TSTIOの960ケース: 6入力×4マスク×Z80/ADL×5幅形、通常／WAIT／CE停止、IRQ/NMI。
- 即値がDD/FD/ED/CB/40/49/52/5Bの場合も1byteのマスクとして消費する追加試験。
- 除外8命令の160ケース: Z80/ADL、幅指定、WAIT/CE停止、レジスタ不変・I/Oなし。
- 拡張ロック中のED74 NEG別名。
- IRX/TIOの実COM各7条件: 通常、CE停止、故障注入、拡張非対応、/RUNなし、旧識別、診断回路なし。
- 既存MEM 9条件、R22.4 MR6/MX6の13条件、WAIT保存・LED、VHDL-93解析を回帰する。

シミュレーションは完全なMSX/Nextor/VDPや配置配線後遅延の再現ではない。GOWIN・実機の本版結果は未確認。
命令名単位の現在一覧は `EZ80_INSTRUCTION_STATUS_R23.md` / JSON。
CALL/JP/RET/RETI/RETN/RSTの形式別制限・未監査項目は継続し、今回のI/O試験だけで全ISA完成としない。

資料: [Zilog eZ80 CPU User Manual UM007715-0415](https://www.zilog.com/docs/UM0077.pdf)。

### 今回の開発側結果

上記の324/960/160/160ケース、実COM各7条件、MEM9条件、MR6/MX6の13条件、WAIT保存・LED、VHDL-93は期待結果でPASS。
TSTIOのIRQ/NMIでは即値直後の復帰PCを明示的に照合した追加480ケースもPASS。
詳細: verification_r23/summary.json と個別verificationフォルダのlog/result.json。
一括再実行: python tools/verify_release_r23.py（GHDL/Icarus環境を指定）。
