# R29：DI_RegからAddress_Regへ続く判定経路の分割

## R28の実測と対象

GOWIN V1.9.12.04、GW2AR-LV18QN88C8/I7。R28 impl_R28.zipより。
Logic16049/20736(78%)、LUT14155、ALU1540、Register6743、CLS9285、BSRAM42/46。
Setup違反395端点、Hold42端点。54MHz系Fmax36.731MHz。
54MHz同一クロック間Setup TNS=-892.467ns（303端点）。
全体の最悪報告余裕はVRAM出力→スプライトCEの-5.671ns。

今回の対象はcpu1/DI_Reg_2_s0/Q→cpu1/u0/Address_Reg_0_s1/D、Setup余裕-4.353ns、54MHz立下り→立上り、関係9.259ns、9論理段。
データ経路遅延の内訳はtC2Q0.232ns、セル4.246ns、配線9.096ns。
先頭LUT3はDI[4:2]のゼロ判定、次のLUT4はDI[7:5]を加えたゼロ判定、その後DI[1]とフレーム制御が合流する。
通常の読出し値をそのままアドレスへ転送する経路だけではなく、復帰フレームのモード値02h／03hの有効判定がアドレス選択を制御していた。

## 変更

1. g80a_ez80.vhd：各入力元の選択後の8bit値Input_Byteを、従来どおりDI_Regへ書き込む。同じprocess・同じ条件でDI_Frame_Valid_Regにbits7:1=0000001の結果を保存する。
2. t80_ez80.vhd：frame_mode状態の02h／03h比較をFrame_Byte_Valid参照へ置換。bit0は従来のDI_Reg(0)を使用。
3. t80_pack_ez80.vhd：内部コンポーネント宣言に同じ入力とgenericを追加。

INPUT_FRAME_PREDECODE=false（CPU単体の既定値）の場合は従来のDIから組合せ判定する。G80Aラッパーはtrueを指定し、保持済み1bitを渡す。
CPU単体を別ラッパーへ接続する場合は既定falseのまま利用できる。trueではDIと判定bitの同時捕捉・同時保持が契約となる。
外部ラッパーのポート変更はない。追加状態は1bit FFであり、PC、レジスタ、アドレス、データのパイプライン段やバス周期は増やしていない。

## 捕捉・保持とWAIT

DI_Regはclk_falling=1、TState=3、BUSAK_n_i=1の立下りで捕捉される。WAIT_nで直接ラッチを禁止しない従来動作を維持する。T3の繰返しがあればデータと判定を同時更新する。
clk_falling=0、TStateが3以外、BUSAK_n_i=0の場合は両方を保持する。
入力元は通常DI、E7E7診断読出し、E6診断I/O、診断IACKの4種類。診断の差替え前ではなく、差替え後のInput_Byteから判定する。
DI_Regに元からリセットはなく、判定FFも同じ保持方針とする。有効なフレーム読出しの捕捉より前に判定を使用する手順は追加しない。
DI_Reg(0)のモード選択、WAITの受付、割込みの受付、混在モード復帰フレーム、MBASE窓、MSX16bitバスの遮断は変更しない。

## 検証

- 全入力256値×入力元4種類×WAIT2条件=2048捕捉。捕捉停止3条件=6144保持。合計8192チェック。
- VHDL93でCPU関連6ファイルを解析。GHDLで通常・診断・拡張無効の3モデルを生成。
- 実機用COMを読み込む既存RUNALL対象25本と、MEM／WIN／IRQ／NMI／TIO等のストレス回帰。
- sim/reference_r28内の完全なR28 CPU6ファイルから独立に参照モデルを合成し、バス波形を全54MHz立上り・立下りで比較。通常9条件、CPU_DIV4・位相3・CEN停止のストレス7条件。
- 詳細はR29_VALIDATION.json。シミュレーションのPASSはGOWINのタイミング保証を代替しない。

既存のR27/R28名のベンチ・スクリプトもR29で新規合成したモデルを使用する。参照モデルはR29では完全なR28ソースであり、古い検証結果の流用ではない。

## GOWINでの確認

DI_Frame_Valid_Regが独立したFFへ実装され、CPUの復帰フレーム判定へ接続されたことを確認する。
比較回路はDI_Regの後ろから入力FFの前へ移る。DI入力／診断MUX→DI_Frame_Valid_Reg、同FF→Address_Reg／SPL等の新しい経路を評価する。
通常DIデータ、bit0、他のアドレス演算・インデックス変位の経路は残る。全DI_Reg経路を解消したとは扱わない。
CPU内部のレジスタ書込み制御、VRAM→スプライト、SDRAMへのHold違反は今回の直接変更対象外。
制約緩和・multicycle・false_pathの追加はしていない。GSR利用は保留を継続する。
