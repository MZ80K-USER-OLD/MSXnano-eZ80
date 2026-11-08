# R11.7 Writeデコード分離

## 基準の実測経路

R11.6のimpl(6).zipでは、先頭Setupが `cpu1/u0/IR_1_s0/Q` → `mcode/Write_Z` → `cpu1/Request_Extended_s0/D`。54MHz上昇→下降の関係9.259nsに対し、データ遅延13.219ns、12論理段、Slack−3.992ns。要求上位バンクにも同じWrite判定を経由する違反がある。

R11.6の報告にはIR→Request_MSX_Addressの−3.803ns、IR→上位レジスタの−4.257nsもある。今回のWrite分離だけでこれらを含む全CPU経路が解消するとは判断しない。

R11.6で要求保持後のVector選択をT1へ移した効果は一部あったが、Writeデコードを捕捉する入力側へ長い経路が移った。R11.7はこのデコード構造を見直す。

## 変更と捕捉・保持

従来のマイクロコードにはZ80デコードの後ろへ各eZ80命令のWrite上書きが順に追加されていた。R11.7は追加命令のWrite代入をこの処理から外し、従来Z80用Legacy_Writeと専用の追加命令Write判定に分ける。他の48出力の命令動作は変更しない。

Classify_Writeはraw opcodeだけから8bitの分類を作る。下位4bitは通常命令、上位4bitはED命令の分類で、ISetと幅フラグは実行側で判定する。この分類をIRと同じ立上り・同じ有効条件で捕捉する。リセット、割込み時のFF/00注入、通常の命令受入れ、DD/FD CBの受入れを含む全5か所を更新し、IRだけ変わる経路を残さない。

命令の分類はIRと同じ期間保持される。MCycle、Data_Long、Stream_Long、ADL_Mode、Has_Width、Branch_Condition、IntCycle、NMICycleで、そのサイクルのWriteを決定する。Writeの出力自体に1サイクルの遅延を挿入していない。命令別の書込みサイクル、WAIT中の保持、IRQ/NMIの受付時点は既存どおり。

IRQ/NMI時の専用上書き、未実装の混在フレーム保護、ADLでのRETN別名保護、拡張ゲートが閉じた場合、Mode 1～3の既存動作も分離前と一致させる。

## 分類表

| nibble | 通常命令の分類 | ED命令の分類 |
|---|---|---|
| 0 | その他 | その他 |
| 1 | LD (nn),HL | ペア絶対書込み |
| 2 | LD HL,(nn) | ペア絶対読出し |
| 3 | LD (nn),A | ADC/SBCペア演算 |
| 4 | LD A,(nn) | MLT |
| 5 | PUSH | LEA |
| 6 | POP | PEA |
| 7 | EX(SP),HL/IX/IY | 未対応RETN別名 |
| 8 | ADDペア演算 | RETI/RETN |
| 9 | 絶対JP | Iレジスタ転送 |
| A | CALL | — |
| B | 条件付きCALL | — |
| C | RET | — |
| D | 条件付きRET | — |
| E | RST | — |

## 検証範囲

保存したR11.6マイクロコードをReferenceとしてGHDLで比較する。opcode256×ISet4×MCycle8×256プロファイル×Mode4 = 8,388,608通り。プロファイルの8bitはExt_Active、Data_Long、Stream_Long、ADL_Mode、Has_Width、Branch_Condition、IntCycle、NMICycle。Writeだけでなく全49出力を比較する。

F、XY_State、Interrupt_Modeは変化させるが、これら3項目の独立した全組合せは網羅しない。Legacy_Writeの計算は元のものをそのまま保持しており、今回分離する追加命令Writeはこれら3項目に依存しない。実CPU回帰で命令受入れ・保持・割込みとの関係を別途確認する。

故障注入ではopcode32hの分類を意図的に0へ壊し、Write不一致を検出する。ソース再生成はdoc/r11_6_baselineの3本から一時ディレクトリで行い、配布RTLとのバイト一致を確認する。生成スクリプトは既に変更済みのRTLへ重ねて適用しない。

## 変更しない部分と未確認項目

G80Aラッパ、top、ブリッジ、SDRAM、VDP、SDC、CST、GPRJ、元のG80Aは変更しない。16bit MSXと24bit拡張バスは分離を維持する。拡張xxFFFFアクセスはMSXアドレス0000h・MREQ無効で遮断する。

false-path／multicycle指定は追加・緩和しない。クロック遅延を相殺する補正も行わない。R11.7の分類FFの入力経路とWrite出力経路はGOWINで新たに評価する必要がある。RTL比較PASSは物理タイミング達成を意味しない。
