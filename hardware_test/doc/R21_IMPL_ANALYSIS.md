# R21 実機FAILとimpl解析

## 確認した事実

- 実機: EZ80MEM P1: FAIL stage 1 / ADDR=07FFFE EXP=31 ACT=7E。
- 実機: EZ80IO2 /RUNはCASE 0表示後に停止。
- 先に報告されたEZ80MEM PASSはユーザー訂正により取り消し。
- 実機確認済み基準版はR20.6。R21の不具合原因は未確定。
- 対象資料: impl(20261115-065434).zip。
- 配置配線ログには完了とbitstream生成完了がある。タイミング合格を意味しない。
- GOWIN V1.9.12.04、GW2AR-LV18QN88C8/I7。
- レポートの設計パスはfpga/project_eZ80/impl/gwsynthesis/MSXNanoTang20K_eZ80.vg。
- netlistにDiag_IO_Signature等R21追加回路が存在。元RTLの全ファイル一致を証明するハッシュはimplにはない。

## FAILの位置

配布版EZ80MEM.COM（CRC32 0C7D91D6）の最初の検査である。

| COM内PC | 命令 |
| --- | --- |
| 0153 | LD A,31h |
| 0155 | LD.LIL (07FFFEh),A |
| 015A | LD.LIL HL,07FFFEh |
| 015F | LD.LIL A,(HL) |
| 0164 | CP 31h |

この比較に失敗するとstage 1、ADDR=07FFFE、EXP=31になる。
この時点で新IO2命令も、07FFFFを使う後続試験も実行していない。
ブリッジの私有RAM配置では論理07FFFEは物理6BFFFEに対応する。
ACT=7Eは015Fの読出し命令のopcodeと同じ値。取込データが更新されなかった可能性を調べる手掛かりだが、読出し命令のopcode残留を証明しない。
書込み失敗、読込み先の誤り、完了/取込時点の誤りを、表示だけでは区別できない。

## セカンダリスロットとの関係

セカンダリスロットレジスタはメモリFFFFh。I/O FFFFhとは別。
top_ez80.vのexp_slotx_req_r/wはMSX側bus_mreq_n=0、RD/WR、保持された上位/下位FF判定、対象スロット条件を使用する。
拡張メモリ要求ではラッパのA_MSX=0000h、Extended_Window=1を保持し、ブリッジでMSX側MREQを遮断する構成を維持。
I/Oの低位FFhは別のRAM mapperポートFC〜FFのデコード対象になり得る。上位BCを保持するだけでは低位8bitで選択される周辺回路との衝突を防げない。
EZ80IO2の実機診断は低位E6hの内部ループバックで、物理MSX IORQを遮断する。
今回のEZ80MEM最初のFAILはFFFFh境界試験より前。FFFFhを使う後続試験によって今回の先行比較が壊れた、という説明は成り立たない。
ただし過去のサイクルの残留/制御信号の不整合まで未観測のまま否定しない。

## 実装規模とSTA

| 項目 | R21のアップロード資料 |
| --- | ---: |
| Logic | 19446 / 20736 (94%) |
| LUT | 17215 |
| ALU | 1877 |
| Register | 7358 / 15915 (47%) |
| STA Setup違反endpoint総数 | 1547 |
| STA Hold違反endpoint総数 | 42 |
| clock_54m内Setup違反endpoint | 847 |
| clock_54mのFmax | 23.915 MHz |
| 最悪Setup slack | -7.664 ns |
| 最悪Hold slack | -2.817 ns |

.trの最悪Setup経路:
- 始点 cpu1/u0/Write_Class_7_s0 (54MHz立上り)
- 経由 mcode/PreserveC_Z、デコード/選択回路
- 終点 cpu1/Request_Address_16_s0 (54MHz立下り)
- Logic Level=13、Setup Relationship=9.259ns
- Arrival=19.162ns、Required=11.499ns（レポートの丸め値）。
- データ部: cell 6.155ns、route 10.504ns、clock-to-Q 0.232ns。

**R21はBlock_IO2に応じてIRBをA2/AA/A3/ABへ書き換えてから全命令ページのcaseを通していた。**
この書換えMUXがグローバルなopcodeデコード入力へ入るため、新命令の判定が通常命令の経路にも構造上入り得る。
これがR21.1で取り除く対象である。

ただしSTAの最悪経路が実機FAILの原因と確定したわけではない。
CPUのWrite_ClassはCPU許可時に更新され、Request_Addressは下降側のCPU許可とT1で捕捉される。
topは3.6MHz相当の信号を54MHzでサンプリングし、別々の立上り/立下り許可を生成する。
通常動作で毎54MHz半周期ごとに同じ転送が要求されるわけではない。
一方、許可信号、TState、割込み/リセット、WAIT/停止復帰まで含めた全経路の最短安定時間は、このレポートだけでは証明できない。
よって一律multicycle/false_pathは追加しない。R21.1もSDCを変更しない。

最悪Hold経路はVDP側のclock_27m→SDRAM側clock_108mで、skew=-3.599ns。
他にmem1/sdram_addrやsdram_din_latchedから108MHz側へのHold違反が表示されている。
これらのsdram_addr/sdram_din_latchedはレガシー要求保持レジスタ。拡張要求はext_addr_latched/ext_data_latchedを選ぶ別経路を使うため、これらの表示だけで拡張RAMの故障を証明しない。
逆に、CPUのCE間引きでVDP/SDRAM側のHoldまで安全になるとは言えない。
SDRAMの要求所有権、保持期間、各ff_sdr_seqでの実捕捉条件の追加照合が必要。
今回SDRAMの構造は変更していない。

## GOWIN警告

Diag_Readの組合せprocessがDiag_Activeを感度リストに含めていなかった。
GOWINはEX4749/EX4387で不足信号を補うと報告している。
R21.1で明示的に追加し、RTL/合成の差を減らす。
ただしEZ80MEMの最初のメモリ試験を直接説明する証拠ではない。

## R21.1の位置付け

命令デコードの構造的な退行を除去し、実機で比較する版。
原因確定済み修正、GOWINタイミング改善済み、実機PASS済みとは扱わない。
旧R21と同じ制御出力を持つことを比較試験で確認し、プログラムの意味は維持する。
R21.1が実機でPASSしても、STA違反が解消したとは判定しない。再配置後のimplを再確認する。
