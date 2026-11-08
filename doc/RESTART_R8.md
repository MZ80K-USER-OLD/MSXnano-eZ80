# 再構築R8：LEA／PEA

## 基準と工程

R7のGOWIN合成成功、実機起動、`EZ80MUL P1: PASS`、その後SofaRunからスペースマンボウを起動・プレイできたことをユーザー報告として記録する。
R7のLUT／DSP内訳は未報告。直近のLUT実測報告はR6の82％。
R8のGOWIN合成・配置配線・タイミング・実機動作は未確認。

R3完了後から数えると、R4メモリ、R5算術、R6ブロック、R7乗算、**R8実効アドレスは5番目**。
これはR版番号とは別の数え方。以前の全工程表を照合して確定した総工程数ではない。
この後はADLの命令フェッチ、制御移行、割り込み、混在動作などが残る。

FPGA差分は `G80A_eZ80/t80_ez80.vhd` と `t80_mcode_ez80.vhd` の2ファイル。
元G80A、ラッパー、トップ、メモリブリッジ、SDRAM、GOWINプロジェクト、Dual Purpose Pin／SystemVerilog設定、CST、SDCはR7と同じ。
マルチサイクル指定・false_pathを追加していない。

## 命令

| 命令 | ED後のオペコード | 動作 |
|---|---|---|
| LEA BC／DE／HL,IX+d | 02／12／22 | IXと符号付き変位を加算し、指定ペアへ |
| LEA BC／DE／HL,IY+d | 03／13／23 | IYと符号付き変位を加算し、指定ペアへ |
| LEA IX,IX+d／IY,IY+d | 32／33 | 入力と同じインデックスを更新 |
| LEA IX,IY+d／IY,IX+d | 54／55 | もう一方のインデックスへ |
| PEA IX+d／IY+d | 65／66 | 実効アドレスをスタックへ積む |

変位dは常に符号付き8bit（−128..127）。幅プレフィクスによらず、変位は1バイトだけ取得する。
40h／52h／プレフィクスなしは16bit、49h／5Bhは24bitのデータ幅。
LEAの短い指定は計算結果の下位16bitだけを書き、宛先の上位8bitを保持する。
長い指定は24bitを反映する。計算元のIX／IYは、宛先に指定されている場合だけ変化する。
BC／DE／HLの表裏はEXXの選択に従う。AとF全8bitは保持する。

PEAの短い指定はSPSを使い、上位・下位の順に2バイトを積む。
長い指定はSPLを使い、上位・中位・下位の順に3バイトを積む。
結果として、最終SPの指す低いアドレスからLSB、MSBの並びとなる。
16bit／24bitの各ポインタはその幅で折り返す。PEAはIX／IYとA／Fを変更しない。

公式eZ80 CPU User Manual UM007715-0415、LEA 242–245ページ、PEA 275–276ページ：
https://www.zilog.com/docs/UM0077.pdf

拡張ゲート開放中だけ追加命令として解釈する。
ロック中は元Z80のNOP、NEG、RETN、IMなどの解釈を維持する。
特にED 54／55／65／66は追加命令と元命令の解釈が異なるため、開放中のデコードでは元のフラグ更新・RETN・IM制御を抑止する。
PC=16bit、割り込み用SPS=16bit、別SPL=24bitのままで、**ADL状態やADL割り込みは未実装**。

## 加算器と保持

既存の `Indexed_Address`（IX／IYの変位アクセス用24bit加算器）を共用する。
LEA／PEA専用にもう1個の24bit加算器やDSPを追加しない。
既存レジスタファイルのC読出しポートを、対象命令中だけIX／IYへ切り替える。
計算結果はEA_Resultへ登録し、以後のレジスタ反映・スタック書込みには保持値を使う。
自己更新LEAでも、書き換えた値から再計算しない。

これはRTLの共有構造の説明で、GOWINの物理回路規模を測定した結果ではない。
R8のLUT／DSP／タイミングの成立は合成・配置配線レポートで確認する。

## 捕捉時点とWAIT／IRQ

| サイクル | 動作 |
|---|---|
| M2／T2 | 変位読出しのWAIT受付。解除時にPCを1バイト進める。PEAでは最初のSP減算も同じ解除時に1回 |
| M2／T3 | 読み終えた変位とIX／IYから実効アドレスを計算し登録 |
| LEA M2／T5 | 下位16bitと、長い指定の場合の上位8bitを同時反映 |
| PEA M2末尾 | 減算済みSPのアドレスを最初の書込み用に登録 |
| PEA M3以降／T1 | 保持した実効アドレスの該当バイトを出力データへ設定 |
| PEA書込み／T2 | WAIT中はアドレス・データ・SP・レジスタを保持。解除時だけ次のSPへ進む |
| PEA M4末尾（短）／M5末尾（長） | 最後の書込みを終えて命令終了・IRQ受付 |

PEAのSPは最初の減算と各書込み間の減算で進む。最後の書込み中には、SPは既に最終値となっている。
それを根拠に途中でIRQを受け付けることはせず、最後の書込み完了まで命令を継続する。
LEAのIRQも宛先への反映後に受け付ける。
保存する復帰PCは、変位を含むLEA／PEAの次の命令。途中のバイトや幅プレフィクスへ戻さない。

CPUのCEN停止では捕捉・書込み・SP更新・反映を止める。
立上り／立下りの許可はT-state全期間単位で対にして停止する。
WAIT中はCPUの可視状態全体とEA_Resultが変化しないこと、各PEA書込みが1回ずつであることを検査する。
命令中の全期間をWAITで停止するという意味ではなく、従来T80のT2受付点に従う。

IRQ追加試験は通常Z80 IM1で、SPSへ16bit PCを保存する。
PEA.LでSPLを使っていても、現在のZ80モードのIRQがSPSを使うのは意図した動作。
仮想ハンドラはAF／BC／DE／HLを保存・復元してEI／RETIで戻る。
ADL IRQ、IM0／IM2／NMIの検証完了ではない。

## 実機用テスト

保存済みFLASHまとめの `EZ80LEA.COM` をそのまま使用する。再コピー不要。
4565バイト。SHA256：
fb19b95ed8301e0344dc21184c7f5c3533e7db84eb8576f262e7976c02b3e949


```
EZ80LEA /RUN
```

期待表示は **`EZ80LEA P1: PASS`**。
引数なしのPLANNED表示は機能試験の合格ではない。半角空白1つと大文字/RUNを指定する。

- LEA.Lの24件：IX／IY×BC／DE／HL×4境界。02FFFFh+1、030000h−1、FFFFFFh+1、000000h−128。
- PEA.Lの2件：IX／IY、SPL=050001h、実効アドレス030000hを3バイト積み、SPL=04FFFEhを確認。

専用RAMの結果退避060100h..060102h、PEAスタック04FFFEh..050000h、COM内の低位バッファと通常SPSを使う。
実効アドレスFFFFFFhなどを計算するLEAでは、そのアドレス先のメモリにはアクセスしない。
試験領域の既存内容は復旧しない。MegaRAM／VRAMを直接試験するCOMではない。

不一致ではstageと `ADDR=xxxxxx EXP=xx ACT=xx` を表示する。
ADDRは比較したRAMデータや結果スナップショットの論理アドレス。
LEA結果の破損では `FAIL stage 1`、`ADDR=060102 EXP=03 ACT=02`、
PEA書込みの破損では `FAIL stage 2`、`ADDR=04FFFF EXP=00 ACT=01` を検査する。

DI中にDOS／BIOSを呼ばない。拡張をロックし、SPSとIX／IYを復旧してからEI・BDOS表示・DOS復帰する。
DOS／BIOS側でEIされることを許容する。実機COMはIRQを注入しない。
先行COMは主に長い指定の結果を確認する。短い指定、IX／IY宛先、全フラグ保持、IRQなどは内部追加試験で補う。
PASS後、SofaRunからスペースマンボウを起動して通常動作を確認する。

## シミュレーション

現行集計は `verification_result.json`。

- R7までの回帰66条件。
- 保存済みEZ80LEA.COMの7条件：正常4位相、LEA結果破損、PEA書込み破損、拡張無効。
- 内部実効アドレス試験4条件：位相、追加WAIT長、CEN停止の組合せ。
- R6由来の期待失敗2条件を継承し、幅再取得欠落とIRQ応答抑止を検出。

内部試験は各条件で72ケース：LEA 57件、PEA 15件。
LEAの全10形式×5幅指定、表裏のBC／DE／HL、正負変位と24bit折返し、宛先上位8bit保持、計算元保持、A／F全8bitを検査する。
PEAは16bit／24bit折返し、SPS／SPLの選択・最終値、計算元保持と書込み順序を検査する。
PEAの書込みバスサイクルは37回。これには未割当バンクへ破棄される4回の試験も含む。
未割当FFFFFFh／FFFFFEhへの試験はバスのアドレス・データとポインタを検査し、RAMへの保存成功とは扱わない。
IRQはLEAの反映前とPEA最初の書込みWAIT中に入れ、各処理の完了後に受け付けることを確認する。
保存PC、SPSフレーム、仮想ベクタへの実際の遷移も確認する。

`sim/lea_corners/EZ80L8.COM` は固定SPS・簡易低位RAM・仮想0038hベクタを使うシミュレーション専用。
**実機で実行せず、FLASHにも追加保存しない。**
16bitスタック折返しの試験ではFFFFhを簡易RAMとして扱い、最後にガードを復旧する。
これは実MSXのセカンダリスロットレジスタをRAMとして使えるという意味ではない。実機COMはSPSをこの配置にしない。
高位xxFFFFhのPEAは、既存ブリッジによりMSXの16bitスロット空間から分離される。
既存のVDP優先SDRAM仲裁とCPU WAITは変更していない。

機能検証はGHDL変換、Icarus Verilog、SDRAMモデル、EIを行う簡易BDOS9による。
実MSX-DOS全体・BIOS起動・映像や、配置配線後の遅延を再現した検証ではない。

## 除外方針と再生成

I/Oポート上位00h固定の追加命令は引き続き除外する。
IN0／OUT0、INIM／INDMと反復版、OTIM／OTDMと反復版、TSTIOを専用実装しない。
通常Z80のIN／OUTとブロックI/Oは維持する。
未実装オペコードを例外にする仕組みはなく、元Z80のNOPや別名として解釈される場合がある。

```
python3 tools/rebuild_from_t80.py
python3 tools/extend_r2.py
python3 tools/extend_r3.py
python3 tools/extend_r4.py
python3 tools/extend_r5.py
python3 tools/extend_r6.py
python3 tools/extend_r7.py
python3 tools/extend_r8.py
bash tools/run_checks.sh
```

GHDL／IVERILOG／IVL_ROOT／VVP環境変数で実行ファイルを指定できる。
GOWINプロジェクトは `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`。
過去のRESTART_R1..R7は各公開時点の記録。今回の実機基準と未確認範囲は本書を優先する。
