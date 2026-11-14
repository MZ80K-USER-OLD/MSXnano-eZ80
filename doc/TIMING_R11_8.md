# R11.8 MCycleからWriteへの選択回路

## 実測した問題

R11.7のimpl(7).zipでは先頭SetupがMCycle_1/Q→Write→Request_Extended/D。54MHz上昇→下降の関係9.259nsに対し、データ遅延12.890ns、Slack−3.663ns、12論理段。R11.6のIR起点からMCycle起点へ変わったが、Write結果を順に更新する優先選択が残っていた。CLSも95%に達している。

## 分離する判定

命令種、ISet、幅、ADL、suffix有無、割込み状態から、その命令がLegacy_Writeを置き換えるかを求める。この判定にはMCycleを入れない。書込みを行わない読出し命令や保護対象も、置き換え対象に含める。

書込みを実際に行う条件は「書込み対象命令の条件 AND 共通サイクル条件」のORとして構成する。最後に、置き換え対象でない時のLegacy_Writeと合成する。Write値の順次上書きは行わない。Legacy_Write内部の従来Z80用MCycleデコードは残すため、MCycleを起点とする全経路を取り除いたという意味ではない。命令選択部分にMCycleが入り込まないことをソース検査でも確認する。

| 共通条件 | MCycleの値 | 主な用途 |
|---|---|---|
| pair_cycle | Stream_Long=0で4～7、1で5～7 | 絶対ペア書込み |
| absolute_cycle | Stream_Long=0で4、1で5 | 絶対バイト書込み |
| push_cycle | 2、3、4 | long PUSH、ADL割込みフレーム |
| tail_cycle | 5、6、7 | EX(SP)、native CALL |
| pea_cycle | 3～7 | PEA |
| rst_cycle | 2～7 | native RST |

到達しないMCycleを勝手にdon't-careにはしていない。元のデコーダと同じ真理値を0～7すべてで維持する。サイクル条件はMCycleの各bitの比較・AND/ORで記述し、整数化、lastaddrの可変演算、順次Write選択をこの経路から外す。

## 優先関係

データ命令のWriteを生成する条件はIntCycle=0かつNMICycle=0を要求する。native CALL／RSTも同じ通常サイクルの条件を持つ。ADL割込みフレームはその反対のIRQ／NMI状態でのみWriteを生成するため、これらのWrite項は競合しない。

suffix付き混在CALL／RET／RSTの保護はLegacy_Writeを遮断するが、ADL割込みフレームのWriteを遮断しない。ADLの未対応RETN別名、RETI／RETNの幅付きフレーム保護、Iレジスタ転送も元の条件のまま維持する。Mode 1～3や拡張ゲートが閉じた組合せもReferenceと比較する。

## 捕捉タイミングと保持

新しいFF、パイプライン段、クロック周期の遅延を追加していない。IRとWrite_ClassはR11.7のまま同じ有効エッジで保持される。要求アドレスと書込み意図はラッパの有効T1下降で捕捉し、WAITやCEN停止中も保持する。Writeの各サイクルでの値をReferenceと照合し、実CPUでもWAIT・割込み・クロック停止を含む回帰を行う。

SDC、CST、GPRJ、CPU本体、ラッパ、ブリッジ、SDRAM、VDPは変更なし。16bit MSXと24bit拡張バスも分離を維持する。拡張xxFFFFはMSXアドレス0000hとMREQ無効で遮断され、bank00:FFFFhは通常どおり。

## 検証と限界

保存したR11.6の元デコーダと、opcode256×ISet4×MCycle8×256プロファイル×Mode4 = 8,388,608通りを比較する。全49出力を照合する。F／XY／IMは変化させるが独立した全組合せではない。分類故障の注入でもWrite不一致を検出する。R11.7のwriterとそれ以外のデコードの境界までのRTLが変わっていないこと、R11.7保存ソースからの再生成が配布ソースと一致することも確認する。

RTL比較と実CPU回帰は物理タイミングの証明ではない。GOWINは論理共有や配置配線を行うため、実際の段数、面積、遅延は新しいレポートで確認する必要がある。他のCPU経路、VDP系、クロック間Hold違反の解消はこの変更だけでは判断しない。false-path／multicycleの追加・緩和やクロック遅延の相殺補正は行っていない。
