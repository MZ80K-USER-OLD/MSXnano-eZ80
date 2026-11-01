# 再構築R6：24bitブロック転送・比較とIRQ／WAIT

## 基準とビルド

R5のGOWIN合成成功、実機でのEZ80ALU P1: PASS、試験後のSofaRun・スペースマンボウのプレイをユーザー報告として記録する。R6のGOWIN合成・配置配線・タイミング・実機動作は未確認。

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を開く。
変更は `G80A_eZ80/t80_ez80.vhd` と `G80A_eZ80/g80a_ez80.vhd`。
元G80A、mcode、ALU、トップ、メモリブリッジ、SDRAM、GPRJ、Dual Purpose Pin／SystemVerilogを含む既存設定、CST、SDCはR5のまま。
マルチサイクル指定やfalse_pathを追加していない。実際のsetup/holdの成立は配置配線後レポートで判断する。

## 実装

| 命令 | 長い指定（49h／5Bh） |
|---|---|
| LDI／LDD | 1バイト転送。HL・DEを24bitで増減、BCを24bitで減算 |
| LDIR／LDDR | 上記をBC全24bitが0になるまで繰り返す |
| CPI／CPD | Aとメモリの1バイトを比較。HLを24bitで増減、BCを24bitで減算 |
| CPIR／CPDR | 上記を一致またはBC全24bitが0になるまで繰り返す |

40h／52hとプレフィクスなしは従来16bit動作。短い指定は上位8bitを保持し、BC下位16bitで終了判定する。
PCと割り込み用SPSは16bit、別のSPLは24bit。ADL状態、24bit命令フェッチ、ADLのCALL／RET／割り込みはまだ未実装。
長いデータ命令をZ80モードで実行している。割り込みでSPSを使うのは現在のモードで意図した動作。

公式eZ80 CPU User Manual UM007715-0415を基準にする：
https://www.zilog.com/docs/UM0077.pdf

転送ではS／Z／Cを保持、H／Nをクリア、PVは減算後のBCが非ゼロ。
比較ではAを保持、S／Z／H／Nは8bit比較、Cを保持、PVは減算後のBCが非ゼロ。
試験では未規定X／Yを除外し、FをD7hでマスクする。
初期BC=0の単発LDIはFFFFFFhへ回り、PV=1となる。16MiBの繰返し全体を完走した試験ではない。

## 内部ループ・割り込み・WAITの関係

元T80の1バイト単位のマシンサイクルを利用する。HL／DE／BCの上位8bitだけを別時刻に先行更新しない。

| 捕捉／反映点 | 動作と停止条件 |
|---|---|
| M1／T3 | BC下位16bitの減算と同じエッジで上位8bitを更新。24bit減算結果から非ゼロを保持 |
| データM2／T2 | HL更新。WAIT_n=0なら保持、WAIT_n=1の1回だけ更新 |
| 転送M3／T2 | DE更新。WAIT_n=0なら保持、WAIT_n=1の1回だけ更新 |
| M3末尾 | 単発命令、カウント終了、比較一致の終了判断 |
| 継続M4／T2 | 反復の再取得先PCを設定。WAIT_n=0なら保持し、解除時に1回だけ戻す |
| 1バイト処理末尾 | IFFと保留INTを評価し、Z80割り込みへ移行。読み書きの途中やWAIT保持中に処理を切らない |

命令幅プレフィクスがある反復はPCを3バイト戻し、幅プレフィクス・ED・命令本体を再取得する。
短い40h／52hも含む。幅プレフィクスがなければ元の2バイト戻し。
継続時のIRQでは幅プレフィクス先頭をSPSへ保存し、終了時は次の命令を保存する。
IRQ後にEDだけを再実行して幅指定を失うことを防ぐ。
この保証の対象は通常の幅プレフィクス＋ED＋命令の並び。冗長DD／FDを混ぜた任意の並びを網羅したものではない。

WAIT試験ではT1から追加WAITを入れ、T2の連続停止中にアドレス・出力データ・上位レジスタ全体・下位レジスタ全体・F・PC・SPS・SPLが変化しないことを検査する。
CPU許可の停止はT-state全期間単位で、立上り／立下りを対にして止める。
CPUレジスタ更新と、ブリッジの1要求1完了を区別する。転送先データ、終了ポインタ、BC、SPL、保存PCを合わせて検査する。
VDP優先のSDRAM仲裁とCPU WAIT、MSXの16bitバスと拡張24bitバスの分離は既存実装を維持する。
高位バンクのxxFFFFhはMSXのセカンダリスロットFFFFhへ流さない。

### 従来ラッパー由来の応答抑止

元ラッパーの `IReq_Inhibit <= not IORQ` は、通常I/Oの不要パルス抑止に加えて、割り込み応答サイクルのIORQも抑止していた。
IM1の内部ベクタ遷移自体は進むので、ゲーム起動だけではこの問題を発見できない。
R6のeZ80ラッパーでは、通常I/Oの抑止を残しつつ、IntCycle_n=0の間は割り込み応答を許可する。
元G80Aファイルは変更しない。検査は内部IntCycleへの移行と、外部M1／IORQ応答と、0038hへの実際の遷移を別々に確認する。
これはIM1試験の結果で、IM0／IM2／NMIやADL割り込みの検証完了を意味しない。

## 実機用テスト

FLASHまとめにある `EZ80BLK.COM` をそのまま使う。再コピー不要。
3505バイト、SHA256：
`b81adadf000c1309df5aa168e1470be55258e02cea6a9e6a5ebd6a33e1907a4a`

```
EZ80BLK /RUN
```

期待表示は `EZ80BLK P1: PASS`。
引数なしのPLANNED表示は機能試験の合格ではない。
単発LDI／LDD、LDIR／LDDR各3バイト、CPI、2バイト目で一致するCPIRを行う。
010001h／010000hからのBC減算で上位と下位の判定を区別し、02FFFFh↔030000hと08FFFFh↔090000hの境界を通る。

不一致では `ADDR=xxxxxx EXP=xx ACT=xx` を表示する。
データ、レジスタの退避先、フラグのバッファなど、比較した値の論理アドレスであり、バス波形の表示ではない。
破損注入試験では `FAIL stage 1` と `ADDR=08FFFF EXP=31 ACT=30` を確認する。

専用RAMの試験領域：02FFFFh..030001h、08FFFFh..090001h、結果退避060100h..060108h、COM内の低位バッファと通常SPS。
物理配置は専用RAMの論理アドレス+640000h。VRAM／MegaRAMはこのCOMでは直接試験しない。
試験領域の既存内容は復旧しない。
DI中にDOS／BIOSを呼ばない。拡張をロックし、SPSとIX／IYを復旧してからEI・BDOS表示・DOS復帰する。
DOS／BIOS側がEIすることを許容する。通常MSXの割り込みを実際に注入するCOMではない。
PASS後にSofaRunとスペースマンボウで通常動作を確認する。

## シミュレーション

`verification_result.json` が現行集計。R5までの回帰46、保存済みEZ80BLKの6、内部ブロック試験の4条件を実行する。
前者には正常実行に加え、故障注入時の診断と拡張無効時のUNSUPPORTEDを含む。
内部ブロック試験は各条件で15ケース、9回のIM1割り込みを実行する。拡張をロックした通常Z80のLDIR／CPIRも含む。独立した期待値でデータ、BC／HL／DE、A／F、SPL、IRQ回数とSPS上の復帰PCを検査する。
読出し・書込みに加え、比較後と反復M4の内部サイクルにもWAITを挿入する。幅プレフィクス取得中、読出し／書込みWAIT中、最終バイト読出し中にINTを入れ、DIでは受け付けないことも検査する。
CPD、CPDR、一致・不一致、単発・反復、24bit境界、短い指定の上位保持も含む。

内部の `sim/block_corners/EZ80B6.COM` は0038hベクタ・固定SPS・低位RAMを模擬する専用フィクスチャ。
**実機で実行しない。** 実機のBIOSベクタを書き換えたり、FLASHへ追加保存したりする必要はない。
IM1ハンドラはAF／BC／DE／HLを保存・復元し、EI／RETIで戻る。システムコールは呼ばない。
幅再取得を無効にした場合と、IRQのIORQ応答を再び抑止した場合の2つの期待失敗も検査する。

GHDLのVerilog変換、Icarus Verilog、簡易BDOS9とSDRAMモデルによる機能検証。
実MSX-DOS全体、BIOS起動、映像出力、GOWIN実装後の遅延を再現したものではない。
ADL割り込みの安全性や全命令の完成は主張しない。

## 再生成と確認

```
python3 tools/rebuild_from_t80.py
python3 tools/extend_r2.py
python3 tools/extend_r3.py
python3 tools/extend_r4.py
python3 tools/extend_r5.py
python3 tools/extend_r6.py
bash tools/run_checks.sh
```

GHDL／Icarus Verilog／vvpを使用する。必要ならGHDL／IVERILOG／IVL_ROOT／VVP環境変数で実行ファイルを指定する。
過去のRESTART_R1..R5文書は各リリース時点の記録。今回の差分と現状は本書を優先する。
