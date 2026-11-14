# R11.10 上位レジスタの共通書込み

## 実測基準

R11.9のimpl(9).zipはLogic17830/20736（86%）、LUT15632、CLS9735/10368（94%）、BSRAM43/46。54MHz系Fmax35.123MHz、同クロックSetup TNS−1165.210ns／291端点。全体Setup619、Hold42端点で未達。

先頭経路はMCycle_1_s0/Q→IORQ_n_i_s0/CE。上昇→下降の9.259nsに対しデータ14.204ns、11論理段、Slack−4.976ns。400件のSetup一覧の最悪報告はExtensions_Enabled_s0/Q→Upper_Upper_RAMREG_3_G[0]_s0/Dで、上昇→上昇18.518nsに対しデータ25.426ns、Slack−6.942ns。先頭HoldはVDP FF_VIDEO_DH_CLK/Q→mem ff_sdr_seq_2/D、27MHz→108MHz、−2.727ns。

SD端点が最悪400件から見えなくなったことだけではSD経路の達成を証明しない。機能PASSもSTA達成を意味しない。

## 変更と捕捉エッジ

今回の変更はCPUのUpperだけ。8個×8bitの上位レジスタへ向かう通常更新のインデックスとデータを1本へ集約する。動的書込み口の重複と優先選択の深さを減らす狙いだが、論理合成・配置配線によって逆効果の可能性もある。GOWIN実測で採否を判断する。

| イベント | データ | 元と同じ捕捉条件 |
|---|---|---|
| 絶対ペア読出し | DI_Reg | 最終上位バイトのT3、長データ、SP以外 |
| LEA | EA_Result上位 | LEA_Commit、長データ |
| ADD／ADC／SBC | Arith_Result上位 | Arith_Commit |
| EX(SP),rr | EX_SP_Read上位 | EX_SP_Result_WE |
| ブロック更新 | Block_Inc_Result上位 | BCはM1/T3、HL／DEは有効データT2 |
| INC／DEC | 旧Upper±1 | M1/T3、下位16bitの境界時 |
| POP | DI_Reg | M4/T3、SP以外 |
| 即値ペア | DI_Regまたは0 | M3/T3またはM4/T3、幅指定に従う |

いずれもRESET非アクティブかつClkEn有効の上昇エッジで捕捉する。新たな保持段はない。DI_Reg等は旧コードと同じ値を同じエッジで参照し、WAIT中のT2更新条件とCEN停止を維持する。各イベントのIR／ISet条件は相互排他で、8種類の通常ポートに同時複数要求が来ない。EX DE,HLは旧値から2エントリを同時交換する別処理を維持し、通常書込みをその後に置いて旧優先関係を維持する。

## 検証範囲

verify_upper_r11_10.pyは保存したR11.9コアと配布コアをGHDLでVerilogへ変換し、同じ入力で実行する。通常6ケースと故障2ケース。Upper64bit、PC、SPL、F、外部出力を両エッジで比較する。8通常イベントの累積カバレッジFFh、交換も実行。命令群のopcode256×ISet4の排他検査は通常イベントが最大1個であることを確認する。これは全内部状態を網羅する形式検証ではない。

全体回帰は254正常ケース＋16故障検出。実MSXスロットRTLの故障検出と拡張要求の保持、WAIT／CEN、割込み、EX(SP)、SD選択番号保持も継続する。20COMは同一バイト列。

## 次の実測

同じGPRJで合成・配置配線し、Upper入力、MCycle→IORQ/RD/MREQ、要求捕捉、VDP、SD選択番号入力と読出し段、27→108MHz Holdを再評価する。R11.9とR11.7を比較基準として残す。R11.10はGOWIN／実機未実施。バス制御経路とVDP・クロック間Holdは今回変更していない。SDC／CST／GPRJに変更なし。一律の例外追加、制約緩和、クロック遅延相殺は行っていない。
