# R30：実行側の命令再判定を減らす第1段階

## 基準と変更範囲

基準はR29.2。ユーザー実機で診断MX0/MX1/MX2/MA1、RUNALL全項目、SOFARUNからスペースマンボウ起動・PLAYが成功し、Logic78%と報告された版。
R29.2の合成後FSM1024条件検証もPASS。ただし配置配線タイミングは未収束（Setup572、Hold42）。機能確認とタイミング保証を区別する。

FPGAの変更は t80_pack_ez80.vhd と t80_ez80.vhd の2ファイルのみ。ラッパー、メモリブリッジ、16bit MSX／24bit拡張バス分離、MBASE窓、VDP、SDC/CST、プロジェクト設定は変更しない。

## 確定する制御

既存54bitのExec_Controlを62bitへ拡張。追加8bitを既存のDecode_Execution呼出しでIRと同時に確定し、同じ許可条件で保持する。命令を進める追加Tステートはない。

| 制御 | デコード時の判定 | 実行側の用途 |
|---|---|---|
| EC_PAGE_BASE | 最終命令ページ00 | 絶対ペア転送のペア番号、24bit演算の対象とADD種別 |
| EC_PAGE_ED | 最終命令ページ10 | 24bit ADC/SBCのキャリー利用、減算選択 |
| EC_IND_OPPOSITE | 命令31/3E | LDペア間接転送のIX/IY反対側選択 |
| EC_EA_SOURCE_IY | 命令03/13/23/33/54/66 | LEA/PEAの基底IY選択 |
| EC_EA_TARGET_IX | 命令32/54 | LEAのIX書込み先選択 |
| EC_EA_TARGET_IY | 命令33/55 | LEAのIY書込み先選択 |
| EC_JP_INDIRECT | 拡張有効・基本ページ・E9 | JP(HL/IX/IY)の拡張処理 |
| EC_SP_IMMEDIATE | 基本ページ・31 | SP即値ロードのSPL書込み経路 |

保持許可を確認する幅プレフィクス試験の観測幅も、旧53bitから現行62bit全体へ修正した。これにより新規制御もWAIT/CEN中に保持されることを検査する。

8bitは追加論理情報の幅であり、GOWINで物理FFが必ず8個増えるという意味ではない。合成での統合・最適化は実レポートで判断する。

## 捕捉タイミングと保持

- 通常：M1/T2、WAIT解除かつ既存ClkEn成立時。Dec_Op・Dec_Page・Dec_XYと、有効なデータ幅／ストリーム幅から確定する。
- DD/FD CB：既存の最終命令捕捉（M7/T2）でも同じ関数を用いる。プレフィクス単独を完成命令として扱わない。
- フレーム終了のNOP注入：既存のDecode_Execution(NOP...)と同時更新。
- RESETでは既存と同じ全0。WAIT、CEN停止、フレーム動作中は既存許可条件以外で更新しない。
- AlternateやFなど命令実行で変化する状態は固定しない。キャリー値自体をフェッチ時に先取りせず、利用するかどうかだけ保持する。
- IRのレジスタ番号フィールドは配線として残す。フィールドの参照と、命令種別の比較器による再判定は区別する。

## 今回の段数への影響

移した箇所は「IR／ISet → 比較・OR → 選択 → 実行先」から「保持済み制御 → 選択 → 実行先」にする。命令比較は制御FFのD側へ移動する。
ただし合成最適化、配置、配線による実際の段数・LUT・遅延は未測定。3段命令パイプラインではなく、複数命令の同時処理もしない。
R29.2のDI_Frame_Valid_Reg入力経路やRegsU書込みCE経路を、この変更だけで解消したとは扱わない。

## 残す判定と次の候補

- t80_mcode_ez80.vhd の命令・MCycle/TState別制御生成は今回維持。
- 割込み受付境界のPrefix／Width_Pending判定は動作上必要であり、完成命令の実行選択と分離して維持。
- 分岐条件、WAIT、CEN、BUSREQ、割込み到来などの動的判断は実行時に行う。
- NextIs_XY_Fetch、旧Modeの即値上位バイト処理、フラグ処理などにはIR／ISetによる比較が残る。今回ですべての再判定をなくしたわけではない。
- 次はGOWIN実ネットリストとSetup/Holdを比較してから、残る選択を移す。使用率や遅延が悪化する場合は本版の差分だけを戻せる。

## 実機確認

GOWINプロジェクトは fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj。別フォルダへ展開し、既存implを流用せず再ビルドする。
COM30本とRUNALLはR29.2から変更なし。書込み済みCOMをそのまま使用できる。

```
EZ80MEM /RUN
EZ80MR4 /RUN
EZ80ALU /RUN
EZ80LEA /RUN
EZ80LDH /RUN
EZ80LDX /RUN
EZ80MX0 /RUN
EZ80MX1 /RUN
EZ80MX2 /RUN
EZ80MA1 /RUN
RUNALL.BAT
```

最後にSOFARUNからスペースマンボウの起動・PLAYを確認。GOWINのLogic内訳とSetup/Hold、implフォルダを比較する。
R29.1等の表示はテストCOMの版番号なので正常。R30のGOWIN／実機結果は未確認。
