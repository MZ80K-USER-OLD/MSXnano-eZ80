# R18 実装タイミング監査とクロック階層の修正パッチ

## 結論

アップロードされた `impl(20261111-144114).zip` はR18のRST追加回路（Frame_Rst_Ready等）を含み、GOWIN合成・配置配線・bitstream生成は成功しています。しかし、タイミング成立は未確認の状態です。

**メモリ不一致の根本原因を確定したとは言えません。** 今回は、報告された違反の分類と、実回路に合っていない派生クロック定義2行の修正を行いました。RTL・CST・GPRJ・COMは変更していません。新しいfalse path、multicycle、最大遅延の緩和は追加していません。

クロック階層を反映したSDCで再配置配線し、残る経路を評価するのが次の手順です。この修正パッチだけで実機の不一致やタイミング違反が解消するとは主張しません。こちらではGOWINを実行できないため、修正後のSTAは未実行です。

## 使用資料

- `pnr/MSXNanoTang20K_eZ80.tr`：数値・経路詳細・有効な制約。
- `pnr/MSXNanoTang20K_eZ80.rpt.txt`：配置配線後リソース。
- `gwsynthesis/MSXNanoTang20K_eZ80.vg`：実際に合成されたPLL/CLKDIVとレジスタの接続。
- `MSXNanoTang20K_eZ80_process_config.json`：合成・配置配線設定。
- 配布済みR18の `fpga/top_ez80.v`、G80A、メモリブリッジ、SDRAM RTL：捕捉条件との照合。

ツールはGOWIN V1.9.12.04、GW2AR-LV18QN88C8/I7、レポート内作成時刻は2026-11-11 22:00:30です。ZIPファイル名の時刻から推定したものではありません。

## リソースとSTA結果

| 項目 | 報告値 |
| --- | ---: |
| Logic | 19,250 / 20,736 = 93% |
| LUT | 17,019 |
| ALU | 1,877 |
| SSRAM | 59 |
| Register | 7,351 / 15,915 = 47% |
| CLS | 10,142 / 10,368 = 98% |
| Setup違反端点 | 716 |
| Hold違反端点 | 42 |
| clock_54m同一クロックのSetup違反端点 | 355 |
| clock_54m同一クロックのTNS | -698.852 ns |
| 54MHzに対するActual Fmax | 38.427 MHz |
| 108MHzに対するActual Fmax | 148.187 MHz |
| 27MHzに対するActual Fmax | 66.740 MHz |

716/42はレポートのSTAサマリ値です。詳細表はSetup 400経路、Hold 25経路までしか出力されていないため、これらの表だけから全違反を列挙することはできません。また、Fmaxの値は全クロック間転送や外部SDRAMのI/O成立を保証しません。

Registerが47%でも、**CLSは98%**です。配置・配線・LUTとFFの組合せ制約は厳しく、FFの残数だけで余裕があるとは判断できません。今回の設定はOptimization_Goal=Auto、Run_Timing_Driven=trueです。比較時はまずこの設定を保持してください。

## 1. 先に直すクロック定義

合成ネットリストで次の接続を確認しました。

| 回路 | 入力 | 出力・分周 |
| --- | --- | --- |
| clk_main/rpll_inst | 外部27MHz | CLKOUT → O_sdram_clk_d（108MHz） |
| div2/clkdiv_inst | O_sdram_clk_d | DIV_MODE=2 → clk_54m |
| div4/clkdiv_inst | O_sdram_clk_d | DIV_MODE=4 → clk_27m |

一方、有効なSDCでは27/54MHzをどちらも外部27MHzから直接生成しています。実際に両CLKDIVへ入る108MHzを親に指定していません。

Hold Path1では、送信側54MHzの時計経路はCLKDIV出力から始まり、受信側108MHzだけにPLLの3.599nsが計上されています。この評価にはクロック定義の親階層が影響している可能性があるため、-2.858nsをそのまま物理的なデータ保持不足と断定できません。**正しい階層で再STAしても残る違反は、別途修正が必要です。42件が全て偽違反だという意味ではありません。**

差し替える2行は次です。

```tcl
create_generated_clock -name clock_27m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 4 [get_pins {div4/clkdiv_inst/CLKOUT}]
create_generated_clock -name clock_54m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 2 [get_pins {div2/clkdiv_inst/CLKOUT}]
```

入力27MHz、PLL108MHz、audioの定義はそのままです。27MHzと54MHzの周波数も変えていません。多サイクル指定で違反を隠す変更ではなく、実際の生成元へ記述を合わせる変更です。GOWINでの読込み・伝播結果は再レポートで確認してください。

## 2. CPUのイネーブルで保持される経路

| 経路例 | Setup Slack | 報告された関係・遅延 |
| --- | ---: | --- |
| cpu1/u0/IR_6 → cpu1/RD / CE | -3.753 ns | 54MHz上昇→下降、関係9.259ns、Data Delay12.980ns |
| cpu1/u0/IR_6 → Request_Extended | -3.703 ns | 同じく半周期、Data Delay12.930ns |
| cpu1/u0/IR_6 → Request_Write | -2.910 ns | 同じく半周期、Data Delay12.137ns |

IRはCPUイネーブルに従って更新され、G80のRD・要求ラッチはclk_fallingで限定された捕捉を行います。内部3.6MHzは108MHzを30分周し、54MHzでは15周期相当になります。そのため、全ての上昇→下降の隣接エッジが有効な捕捉エッジになるわけではありません。

ただし、WAIT、I/Oのenable停止、フレームの開始・終了、リセット、全てのIR更新箇所を含めた最短保持期間の証明が必要です。**今回これらへmulticycle/false pathは追加していません。** 15分周という事実だけでCPUから出る全経路を緩和してはいけません。

## 3. 15分周を理由に緩和できない経路

| 経路例 | Setup Slack | 判断 |
| --- | ---: | --- |
| Request_Extended → mem1/sdram_seq[0..2] CE | -2.922 ns | 受信側は54MHzで動く受付FSM。最優先で捕捉条件を確認 |
| Request_Extended → mem1/sdram_write | -2.653 ns | 要求の種別・有効判定へ伝播。上と同じ扱い |

Path22はRequest_ExtendedからメガRAM選択/アドレス分離を経てSDRAM受付FSMのCEへ到達し、データ遅延12.144nsに対して半周期9.259nsです。この経路は同じ54MHz内なので、PLL→CLKDIVの親階層を直すだけで自動的に安全になるものではありません。

受信側FSMはCPUのCENを待たず毎54MHzで動くため、最初の許可された捕捉エッジに間に合う必要があります。スロットの有効条件で必ず遅いエッジだけを捕捉することを証明できない限り、CPUの15分周を根拠に緩和できません。要求validを短い経路で登録し、アドレス/書込データ/所有者を揃えて保持するなど、受付側のパイプライン化・論理整理が修正候補です。

この経路と観測された書き込み取りこぼし/古い読み値には関連の可能性がありますが、直接の因果は未確認です。MSX16bitと拡張24bitの分離は維持し、遮断済みMSXアドレスを拡張要求の元に流用してはいけません。

## 4. SDRAMデータ・VDP制御のクロック間経路

| Hold経路例 | Slack |
| --- | ---: |
| legacy sdram_din_latched[0] → mem1/n1035（DQ出力データFF） | -2.858 ns |
| FF_VIDEO_DL_CLK → SdrSta[1] | -2.451 ns |
| FF_VIDEO_DH_CLK → ff_sdr_seq[1] | -2.396 ns |
| legacy sdram_write → SdrSta[0] | -2.128 ns |

n1035はネットリスト上でSDRAM DQ[0,8,16,24]のIOBUF入力へ接続されています。最悪Holdの送信元はlegacy側のsdram_din_latchedであり、拡張側ext_data_latchedからの直接パスではありません。この違反だけで今回の0A6000アクセスの原因を確定することはできません。

クロック階層を反映した再STA後、スロットごとのデータ保持・書込種別・DQM・読み値の捕捉を確認します。VDPを優先し、競合時はCPUへWAITを返す方針は変えません。

Setupではvram_dout→sprite CEに-6.223nsがあり、既存のset_max_delay=10.5nsも適用されています。これも今回一律に変更していません。VDP側の実際のcapture enableとVRAMデータ保持期間を確認する必要があります。

## 5. このレポートでまだ確認できない点

- Setup400経路の一覧に、Request_Data、bridge ram_din、ext_data_latchedを直接終点とする行はありません。報告件数が限定されているため、無違反の証明ではありません。
- 次の経路の詳細を追加すると、私有RAMの書き込みそのものを追えます：Request_Data→memory_bridge/ram_din、ram_din→mem1/ext_data_sample、ext_data_sample→ext_data_latched、ext_data_latched→SDRAM DQデータFF、ext_write_latched→SdrSta、ext_done→bridge done_sync→WAIT。
- 有効なSDC一覧には、SDRAM外部端子の明示的なset_input_delay/set_output_delayがありません。このレポートだけではSDRAM端子での外部setup/holdを証明できません。使用デバイスのI/O条件・クロック位相に基づく評価が別途必要です。
- 機能モデルは実ゲート・配線遅延を再現しません。15分周や映像クロック位相を変えたRW2の機能シミュレーションでは、実機の最初の31→7Bと55→03は再現していません。別途見つかった映像位相変更時のlegacy/VDP読出し不一致を、今回の私有RAM症状と同一視していません。

## 適用と再確認

1. 現在のR18のソース、SDC、impl、bitstreamを保存します。
2. 同じR18ソースの **fpga/tang20k.sdc** の27MHz/54MHz定義2行を差し替えます。このZIPの同名ファイルは配布R18を基準にした完成版です。手元のSDCに独自変更がある場合はclock_hierarchy.patchの2行だけを反映してください。
3. 同じ `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` で合成・配置配線します。比較のため、Auto/Timing Driven等の設定は今回のレポートとそろえます。
4. 新しいClock Summaryで27/54MHzのMasterがclock_108mになったこと、周期が37.037/18.518nsのままであることを確認します。clock_108mのPLL経路が両CLKDIV側へ適切に伝播したか、Hold詳細のclock pathで確認します。
5. 再生成したimplを解析して残る本当の受付経路・データ経路の修正範囲を決めます。
6. 新しいbitstreamを実機へ適用する場合は、COMを変更せず `EZ80RW2 /RUN` を再実行します。機能改善は未確認なので、表と最後の結果を記録します。

このパッチはタイミングモデルの修正であり、RSTやメモリ故障を修正済みとする新しいCPUリリースではありません。

## 同梱データと検証

- audit_summary.json：資源、STAサマリ、元SDC/修正SDCと入力ZIPのSHA256。
- setup_paths_400.json / hold_paths_25.json：報告された詳細表の機械可読化。
- timing_evidence.txt：上記の重要経路、クロック経路、有効制約の抜粋。
- fpga/tang20k.sdc / clock_hierarchy.patch：27/54MHzの派生クロック2行だけの変更。

合成ネットリストからPLL/CLKDIVの接続とDIV_MODE=4/2を検査し、変更前後の他の有効制約が一致することを確認しました。パッチを元のSDCへ適用し、同梱の修正SDCと一致することを確認しています。GOWINによるパッチ読込み・再STA・実機確認は未実行です。
