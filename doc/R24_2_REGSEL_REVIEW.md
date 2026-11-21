# R24.2 レジスタ選択の共通化検討・比較候補

## 結論

R24.2の汎用レジスタはA/B/C各24bit読み出し、上位8bit補助読み出しU、共通書き込みWへ統合済み。
残る選択番号の生成では、即値ロードとスタックの式は完全に同一であり、HL→IX/IYの変換も複数箇所に現れる。
比較候補ではこの部分を組み合わせ信号にまとめた。レジスタ保持FF、実行制御FF、Tステートは追加しない。

ただし、同じ式はGOWINが既に共有・最適化している可能性がある。VHDLの重複行数の減少はLUT削減の実測値ではない。
候補はR24.2の置き換え確定版ではなく、GOWINで面積・タイミングを比較するためのもの。

## 基準版の実機確認（ユーザー報告）

R24.2：GOWINビルド成功、Logic 96%。EZ80MEM、EZ80MR4、EZ80LDH、EZ80LDXはPASS。
RUNALL.BATはすべてPASS。SOFARUNからスペースマンボウの起動・PLAY成功。
これらは基準R24.2の結果であり、本比較候補の実機結果ではない。

## レジスタファイルの選択番号

| 3bit番号 | レジスタ |
|---|---|
| 000 | BC |
| 001 | DE |
| 010 | HL |
| 011 | IX |
| 100 | BC' |
| 101 | DE' |
| 110 | HL' |
| 111 | IY |

AlternateはBC/DE/HLの裏表を選ぶ。IX/IYはAlternateで切り替えない。
命令のrrフィールド11がSPまたはAFを意味する場合もあるため、この3bit番号に直接読み替えてはいけない。
SPとSPL、ACCとFはこの配列の外にある。

## 比較候補の変更範囲

FPGA入力ソースの変更は `fpga/G80A_eZ80/t80_ez80.vhd` のみ。

```vhdl
Pair_Raw_Index <= Alternate & IR(5 downto 4);
XY_Register_Index <= XY_State(1) & "11";
HL_Resolved_Index <= XY_Register_Index when XY_State /= "00"
                     else Alternate & "10";

Load_Upper_Index <= HL_Resolved_Index when IR(5 downto 4) = "10"
                    else Pair_Raw_Index;
Stack_Upper_Index <= Load_Upper_Index;
EX_SP_Index <= HL_Resolved_Index;
```

絶対アドレスのPair_Upper_Index、Arith_Target/Source、Mul_Targetにもこの共通信号を使う。
Arith_TargetではISet=00だけHL置き換えを認め、EDページでは元のHLを維持する。
Mul_Targetは元と同じ未置換のPair_Raw_Indexを使う。

新しい3本は組み合わせ信号であり、3本のFFを追加したという意味ではない。
VHDL関数にまとめるだけでも、呼び出しごとに論理が展開され得る。本候補は共通信号として記述するが、
合成器は配置や遅延の都合で複製できるため、物理回路の共有量はネットリストで判断する。

## 一律に置き換えてはいけない箇所

| 箇所 | 維持する条件・理由 |
|---|---|
| A/Bの通常選択 | XY_Ind=0のときだけ通常のHL→IX/IY置き換えを行う。既存の保持アドレスを残す |
| RegAddrAのINC/DEC選択 | XY状態・サイクルに依存し、不該当時はRegAddrA_rへ戻る。無条件のペア選択に変えない |
| RegAddrC | JP(HL)/LD SP,HL、M6の強制選択、間接転送、LEAなどの優先順位を維持する |
| EDのADC/SBCなど | DD/FD状態だけでHLをIX/IYへ置き換えない |
| LDH/LDXの間接転送 | アドレス元と転送レジスタは別。IR=31/3Eなどの逆側IX/IY選択も通常のHL変換とは別 |
| EX DE,HL | 表裏選択と交換のT3/T4を維持する |
| SP/SPL | Data_Longなど、その処理に対して確定済みの幅を使う。ADLだけで選ばない |
| 上位バイト書き込み | 読み出しAが次の選択へ進んでも、Load_Targetなどに保持した書き込み先を使う |

これらの保持タイミングを揃えずに、単一の「現在選択レジスタ」へ統合すると、以前の上位バイト誤書き込みを再発させる危険がある。
候補ではA/B/Cの保持回路、U補助ポート、Load_Target、Reg24AddrWの優先順位を変更しない。

## 読み出しポートを1本にできるか

A/B/Cは同時に別レジスタを読むためのポートで、同じ種類のMUXでも同一ハードウェア1本へ置き換えられるとは限らない。
たとえば24bit算術はA/Bの両オペランドを同じT4で捕捉する。
1本化には時間分割とオペランドの先行保持が必要で、FF・制御・サイクルの増加を含めて比較する必要がある。
U補助ポートもスタックと絶対アドレス転送の上位出力に使われており、既存A/B/Cの空き時刻の証明前には削除しない。

したがって今回の候補は「選択番号を作る前段の共有」であり、レジスタ読み出しMUXの本数を減らす変更ではない。
大幅なLUT削減を見込む根拠はなく、小幅な削減または同等、最適化によっては増加もあり得る。

## 検証

`tools/verify_regsel_compare.py` は、同梱した基準R24.2のコアと候補を別々にGHDLで変換し、同じ入力で並行実行する。
基準コアは `sim/reference/r24_2_regsel/t80_ez80.vhd.txt`。
他のCPU VHDLは基準と変更していない。

* 両ソースから選択式を抽出し、IR 256 × ISet 4 × XY_State 4 × Alternate 2 = 8192組の選択結果を照合。
* 既存D3/MEM/ALU/BLK/LEAのCOMを用いる5系統、拡張無効のD3を1系統。
* LDH/LDXの単体試験を各3条件（WAIT+CEN停止、IM1、NMI）で照合。
* 各クロックの立上り・立下り後に選択番号、書き込み先・マスク・データ、PC/SP/SPL/A/F、上位レジスタ状態、外部バス出力を照合。

今回の結果：選択式8192組は全一致。12条件の差分シミュレーションは全PASS、5,728,308回のクロック端照合で不一致なし。
CPUのVHDL 6ファイルはVHDL-93解析もPASS。

結果の正確な件数とソースSHA256は `verification_regsel_compare/result.json` に収録する。
これはモデル上の差分検証で、全命令網羅、実BIOS/DOS起動、GOWINでの等価性証明ではない。

実行例：`python3 tools/verify_regsel_compare.py`
GHDL、Icarus Verilog、vvpが必要。必要に応じGHDL/GHDL_PREFIX/IVERILOG/IVL_ROOT/VVPを環境変数で指定する。

## GOWINでの比較方法

両版の `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を、同じIDE版・デバイス・合成/配置配線設定でビルドする。
候補ZIPにはこのプロジェクトと既存の実機用COMを含む。
以前のimpl生成物を持ち込まず、各版で独立して生成する。

比較項目はLogic実数、LUT/ALU内訳、FF、CLS、最悪Setup/Holdとその端点。
Logicの表示パーセントだけでは小さな変化を判別できない。
合成後.vgのMUX2_LUT5/6等の数も調べるが、専用MUX数を消費LUT数へ加算しない。
候補は組み合わせ論理の書き換えだけなので、設定や制約の緩和によって差を作らない。

採用はLUT削減とタイミングの比較後に判断する。増加または実機回帰があれば基準R24.2へ戻す。
基準への復帰は基準ZIPを別フォルダへ展開するか、同梱patchを逆適用する。

既存COMは変更しない。新しい実機テストをFLASHへ追加する必要はない。
GSR利用は保留のまま。16bit MSX/24bit拡張アドレス分離、メモリ接続、WAIT処理、命令・割り込み制御も変更しない。

## 検討の優先順位

1. 本候補で選択番号生成の小規模な共有がGOWINでも有利か確認。
2. 効果がなければ同じ式の整理を続けず、書き込みデータ側の選択や補助読み出しポートの使用時刻を調べる。
3. 実行デスクリプタにレジスタ番号を追加保持する案は、FFと選択論理を増やす可能性があるため別比較にする。
   R24でデスクリプタを増やした際のLogic増加を踏まえ、今回には混ぜない。
