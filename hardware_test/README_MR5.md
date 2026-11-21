# MR4のLINK後停止を調べる診断 — EZ80MR5

**現在のR22.2ビットストリームをそのまま使う。FPGAの再ビルドは不要。RTLやGOWIN設定・制約は変更していない。**
今回の実機報告は、MR4でSTART、LOCAL EXP=31 ACT=31、LINK EXP=55/AA ACT=55/AAまで表示され、その後の行が報告されていない状態。
LOCALの1byte比較とLINKの固定値選択は成功。これを拡張RAM全体や記録データ本体の正常性の証明にしない。

## 実行

ZIP直下のEZ80MR5.COMを実機のDOSドライブへコピーし、再起動後に実行する。

```
EZ80MR5 /RUN
```

最後の期待表示は `EZ80MR5 R22.2: PASS`。/RUNなしではREADYのみ。旧機能識別ではNOT READY/UNSUPPORTEDに戻る。
COMは3544bytes、CRC32 **E863F1C9**。hardware_testにも同一COMを収録。
失敗や停止を含めて実機では未確認。今回の配布は原因切り分け用であり、フリーズ修正完了を意味しない。

## 元のMR4で表示されない区間

LINK後、拡張を再有効化し、HL=010100を設定、010100への絶対書込31、絶対読出2回、HL間接読出2回、HLのMSX RAMへの保存、W/R記録の取得・照合・文字列整形を実行してから次の行を表示する。
従ってLINKが最後でも、最初の書込で停止したと断定できない。再アンロック、レジスタ操作、記録取得やDOS復帰も候補に残る。

## MR5の進捗

標準的な成功表示は次のとおり。W0以降の物理アドレス650100は、論理010100に対応する。

```
EZ80MR5 R22.2 START
LOCAL EXP=31 ACT=31
LINK EXP=55/AA ACT=55/AA
BEFORE_LDHL
HL_SNAPSHOT_DONE
HL ACT=010100 EXP=010100
BEFORE_WRITE
WRITE_DONE
BEFORE_WRITE_TRACE
W0=650100/31
WRITE_TRACE_DONE
BEFORE_A1
A1_DONE
BEFORE_A2
A2_DONE
BEFORE_I1
I1_DONE
BEFORE_I2
I2_DONE
BEFORE_SNAPSHOT
SNAPSHOT_DONE
BEFORE_TRACE
TRACE_DONE
A 010100 E31 A1=31 A2=31
I1=31 I2=31 HL=010100
W=650100/31 R=650100/31
BEFORE_BURST
B 010100 ECE A1=CE A2=CE
I1=CE I2=CE HL=010100
W=650100/CE R=650100/CE
EZ80MR5 R22.2: PASS
```

| 最後の表示の例 | 絞られる範囲 |
| --- | --- |
| BEFORE_LDHL | 再アンロック、HL24設定、HLのMSX RAMへの3byte保存まで |
| BEFORE_WRITE | 絶対書込と、その後のロック・DOS表示への復帰まで |
| BEFORE_WRITE_TRACE | 書込記録のI/O読出と表示への復帰まで |
| BEFORE_A1 / BEFORE_A2 | 1回目/2回目の絶対読出と表示への復帰まで |
| BEFORE_I1 / BEFORE_I2 | 1回目/2回目のHL間接読出と表示への復帰まで |
| BEFORE_SNAPSHOT | HLのMSX RAMへの3byte保存と表示への復帰まで |
| BEFORE_TRACE | W/R記録取得と表示への復帰まで |
| BEFORE_BURST | DOS表示を挟まない書込・4読出・HL保存・記録取得・照合・表示まで |

マーカーは操作の直前/直後の手がかりであり、単一回路の原因を証明するものではない。各表示後にはDOS復帰、DI、再アンロックがある。
W0はブリッジが受け付けた最後の拡張書込のアドレス/データ。物理RAMに正しく保存された証明ではない。READ結果とR記録も合わせて比較する。
最後のB行は元MR4に近い連続アクセスで、途中にDOS表示を挟まない。A行は各操作でDOSへ戻るため、配置・間隔・割込み時点が元MR4と変わる。
すべてPASSでも元MR4/EZ80MEMの実機回復の証明にはしない。

## 不一致の表示

結果比較で不一致があれば、各行に実際の値を表示し、最後に例えば次を出す。

```
EZ80MR5 R22.2: FAIL
ADDR=010100 EXP=31 ACT=20 (see row fields)
```

ADDRはこの診断の対象論理アドレス。EXP/ACTは最初に不一致となった比較byte。CPUの読出値だけでなくHLスナップショットやW/R記録も検査するため、どの欄が不一致かをA/B行と照合する。
ローカル比較やLINKが不一致の場合も、その行を省略せずに報告する。

## 実行条件

- CPUはZ80モード、MBASE=0で実行。24bitデータ幅・アドレスを指示するprefixを使うが、ADL命令フェッチやADL割込みは使わない。
- 新規ブロックI/O命令は実行しない。D8診断ループバックも有効化しない。
- 拡張RAMの対象は010100の1byte。前半は31、連続アクセスの後半はCEを書込む。
- DOS呼出前に拡張をロック。DOS内部のEIを前提に呼出直後にDIを再実行する。最終的にSP/IX/IYを戻してEIでDOSへ復帰する。
- HL間接読出の前にはHLを毎回設定し、DOS呼出がHLを変更する可能性を考慮する。
- 動作確認済みR21.3も同じ記録インターフェースを持つため、保存済みビットストリームがあれば同じCOMを比較に使える。

## 検証

実COMをR22 RTLからのGHDL変換CPU・ラッパ・ブリッジ・SDRAM制御RTL・SDRAMモデルに接続。R22.2のデコーダ配置変更は別途R22と制御等価性を確認済みだが、今回のソフト検証を配置配線後実機の保証としない。
10プロファイル: 通常、CE停止/位相変更、SDRAM書込データ故障、拡張無効、/RUNなし、旧機能識別、LINK断、記録データ断、最初の書込ACK停止、最初の読出ACK停止。
各DOS印字でEIとIM1割込みを実行し、復帰状態も確認。停止注入2件は試験台で有限時間後に観測を終了する。FPGAにタイムアウト解除機能を追加したのではない。

- 書込ACK停止: BEFORE_WRITEまで、WRITE_DONEなし、WAIT_RAMでWAIT保持。
- 読出ACK停止: WRITE_DONEとW0表示の後、BEFORE_A1まで、A1_DONEなし、WAIT_RAMでWAIT保持。
- 書込値を20に変える故障: ADDR=010100 EXP=31 ACT=20を検出。
- 記録を0にする故障: CPU値が正しくてもW/Rの不一致とEXP/ACTを検出。

ログと集計はverification、ソース等はhardware_test/sim/toolsに同梱。新しいビットストリームやFPGAソースは含めない。
生成はhardware_testで `python build_mr5_r22_2.py`。build_data_r3.py/build_mr4_r21_3.pyは生成用参照ファイルなので直接実行する必要はない。
シミュレーションは既存R22系プロジェクトへ対応ファイルを置き、CPUモデルを生成後tools/verify_mr5_r22_2.pyを実行する。GHDL/Icarusのパス設定が必要。

## 次に必要な実機結果

最後に表示された行、表示できた場合のW0行とA/BのW/R行を保存する。これにより、要求前・完了待ち・読戻し・記録取得・連続アクセスのどこへ調査を進めるかを決める。
