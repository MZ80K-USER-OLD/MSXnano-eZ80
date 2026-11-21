# R22.3 WAIT停止状態の保存とLED表示

R22.2をベースにした実機診断版。根本原因の修正版ではない。
CPU命令デコード、16bit/24bitバス分離、SDRAM調停、WAIT生成条件、SDC/CSTは変更していない。
通常のキーボード状態LED表示を、CPUから独立した診断表示に切り替える。

## 実機手順（最初は4ページだけでよい）

1. ZIPを完全に展開し、この版の `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を開く。
   既存版のimplを流用せず合成・配置配線し、生成されたイメージを実機へ書き込む。
2. 再起動後、同梱の `hardware_test/EZ80MR5.COM` を `EZ80MR5 /RUN` で実行する。
   COMは前回配布したMR5と同一。3544 bytes、CRC32 **E863F1C9**。
3. 画面が停止したら、S1リセットを押さず、まず基板の6灯を撮影する。
4. **S2を1回押して離し、1秒待って撮影**する。これを計3回行う。
   最初と合わせてページ0、1、2、3の4枚になる。基板の向きとLEDの並びが分かる写真にする。
5. 画面の最終表示、LED4枚、GOWINのLogic使用率を報告する。
   LED5が点滅したままなら、その状態も報告する。停止したからといって必ず記録があるとは限らない。

ページ4以降のアドレス記録は、最初の4ページで必要と判断してから取得してよい。
連続した動画でもよいが、各S2操作の間は1秒以上空ける。
S2は既存UARTデバッグ送信にも接続されたまま。元の接続を変更していない。

## LEDの読み方

LED番号は `fpga/tang20k.cst` の信号番号。
LED0=FPGA pin20、LED1=19、LED2=18、LED3=17、LED4=16、LED5=15。
左右の向きは写真や基板上の表示で照合する。
Tang Nano 20KのLEDはactive-lowなので、以下の「1」は点灯を意味する。

| 状態 | LED5 | LED4 | LED3..0 |
|---|---|---|---|
| 記録前 | 約0.62秒ごとに反転 | 消灯 | 消灯 |
| 記録直後／S2操作後の約0.5秒 | 点灯 | 消灯 | ページ番号0..F |
| ページ内容の表示中 | 点灯 | 点灯 | 保存値の16進1桁 |

LED0=1、LED1=2、LED2=4、LED3=8として点灯値を合計する。
例えばLED0とLED2だけが点灯なら値5。LED5/4はこの合計に含めない。
S2は押下を安定確認して1ページ進み、長押しで連続送りしない。Fの次は0。
保存は最初の1回だけ。S1リセット／電源再投入で消える。

## 保存条件と範囲

54MHzの実クロックで、マップ対象の拡張MREQが2^20クロック（約19.4ms）連続したときに保存する。
CPU clock-enableやWAITに依存せず動作する。MREQが無効なら、非ゼロバンクが出ていても保存しない。
WAITが解除されたCOMPLETE状態でMREQだけ残る場合も観測できるよう、WAIT低だけには限定していない。
この時間は**観測開始のしきい値**であり、WAITを解除するタイムアウトではない。
正当に長い要求も保存され得るため、記録だけで欠陥を確定しない。

64bitを一度だけ保存する。ページ0が最下位4bit、Fが最上位4bit。

| ページ | LED3..0（左がbit3） |
|---|---|
| 0 | ram_done、ram_req、bridge state[1:0] |
| 1 | done_sync、done_meta、ext_wait_n、ram_write |
| 2 | Extended_Window、WR_n、RD_n、MREQ_n |
| 3 | controller ext_sync、ext_pending、ext_selected、ext_running |
| 4..9 | CPU 24bitアドレス。4が最下位桁、9が最上位桁 |
| A..E | 受理済みSDRAM物理アドレスの下位20bit。Aが最下位桁 |
| F | wait_io、物理アドレス[22:20] |

bridge stateは0=IDLE、1=WAIT_RAM、2=COMPLETE、3=DRAIN。
ram_writeは保持された要求の書込み種別であり、未受理のサイクルでは前回値になり得る。
ram_addrも同様に受理済みの値。CPUアドレスと両方を見る。
done_meta/done_syncはブリッジ既存の同期段。コントローラの4状態信号だけは診断回路で2段同期する。
したがってコントローラ表示は54MHzで2クロック程度遅れ、遷移付近の全信号が厳密に同時とは限らない。
これはバストレースや配置配線後のタイミング測定の代わりにはならない。

最初の4桁で次を区別する。

| 記録 | 調べる箇所 |
|---|---|
| IDLE、WAIT低、reqなし | MREQとRD/WR、前回doneの解除、受理条件 |
| WAIT_RAM、reqあり、doneなし | コントローラの要求同期・pending・slot選択・running・完了 |
| DRAIN、done_syncが残留 | 前回req解除から完了通知解除までの経路 |
| COMPLETE、WAIT高、MREQが継続 | CPUの進行、他のWAIT、wait_ioによるCE停止 |
| LED5が点滅したまま | 本監視条件では保存なし。DOS表示内停止、MREQなし、クロック・リセット等も再検討 |

WAIT_RAMなどの状態名は原因名ではない。まず観測に沿って調査対象を選ぶ。
CPU全体のTState/MCycle/命令レジスタ、全WAIT源、過去の信号波形はこの版では保存しない。

## 開発側の検証

- 実ブリッジ＋診断回路で、通常のwrite/read、MREQなし内部サイクル、RD/WRなし、ACKなし、前回ACK残留、COMPLETEのMREQ残留を試験。
- 保存後の固定、16ページ全表示、ボタンバウンス除外、長押し、ページ巡回、リセットを試験。
- 現在のCPU RTLをGHDLでVerilog化し、実際のMR5 COM＋ブリッジ＋SDRAMコントローラ＋SDRAMモデルで10条件を試験。
  通常・CE停止・データ異常・対応判定・LINK異常・トレース異常・write/read ACK停止を含む。
  DOS stubは表示ごとにEIし、実CPUのIM1割込みを通す。正常時に停止記録を作らないことも確認。
- 既存EZ80MEMの9条件を回帰。
- 対象GPRJの全パス存在と、新規接続部分の限定的なtop elaborationを確認。
  このelaborationでは無関係な周辺回路／ベンダー素子を省略している。
- 全周辺回路を含むIcarus elaborationは、既存のstreaming concatenation等の未対応構文で実行できない。
  GOWIN合成・配置配線・資源量・タイミング・実機結果は未確認。

再実行: `python tools/synthesize_r22.py`、`python tools/verify_wait_monitor_r22_3.py`、
`python tools/verify_wait_mr5_r22_3.py`、`python tools/verify_mem_r4.py`。
ローカル環境に応じGHDL/IVERILOG/IVL_ROOT/VVPを指定する。
LEDの全16桁を取得できた場合は `tools/decode_wait_snapshot_r22_3.py` にページ0..Fの順で渡す。

## 前例との関係

添付された65816風拡張の事例は、アドレス更新予告だけでWAITを立て、要求の来ない内部サイクルで永久待ちした欠陥。
現在はMREQでWAITを条件付けているため、同一欠陥とは断定しない。
今回追加した回路は、その教訓に沿って「どの待機条件で止まったか」を外部から確認するためのもの。
一定回数でWAITを強制解除する処理、制約緩和、命令動作の変更は追加していない。
