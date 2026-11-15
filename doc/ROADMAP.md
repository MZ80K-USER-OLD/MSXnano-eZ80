# Current: R21.3 observation link

R21.2 user hardware: MEM/IO2/RUNALL all PASS, SofaRun Space Manbow PLAY. MR3 observation records zero. R21.3 moves byte selection into Verilog and verifies 55/AA over the same link. New ISA work remains paused until this observation issue is resolved.

# Current: R21.2 diagnostic build

R21.1 hardware memory regression persists. MR2: local/HL match, extended RAM reads wrong in all test rows. R21.2 records bridge write/return values; new ISA work remains paused. See R21_2_README.md.

# Current: R21.1 comparison build

R21 hardware: EZ80MEM stage 1 FAIL 07FFFE EXP31 ACT7E; EZ80IO2 freezes at CASE 0.
R21.1 removes the global opcode rewrite mux. Hardware and GOWIN validation pending.
See R21_1_README.md and R21_IMPL_ANALYSIS.md. New instruction work is paused until the memory regression is resolved.

# 現行：R21

単発IO2の4命令を実装、GOWINと実機は未確認。残る優先順位はREMAINING_R21.md、監査はISA_AUDIT_R21.json。以下は履歴。

# 現行方針：R20.6

SLPは非対応・NOP、TRAPも非対応。実装優先順位は[REMAINING_R20_6.md](REMAINING_R20_6.md)、現行監査はISA_AUDIT_R20_6.jsonを参照。以下は過去の工程記録であり、SLP/TRAPが残項目という旧記述は現行方針では無効。

> R18更新：R17はLogic94%、RUNALL全PASS、D3 R3:PASS、SofaRun/スペースマンボウPLAYを実機確認済み。R18で工程8の正規混在/MADL RSTを追加。ADL IM0・SLP・未定義オペコードの扱い・残I/O監査と工程10は未完。最新詳細はISA_AUDIT_R18.mdとRESTART_R18.md。以下の旧版記述は当時の履歴。

# 現行：restart R17

R16はGOWIN Logic93%、LDH/CT1/D3/TST/MEMと実装済みRUNALL全PASS、SofaRunからスペースマンボウPLAYを実機確認済み。R17でLDXを追加し、既存Indexed_AddressとLDH/EX(SP)の作業レジスタを共用。既存EZ80LDX P2:PASS、RUNALL全PASSを期待し、COM更新は不要。R17のGOWIN/実機/規模/タイミングは未確認。命令監査、ADL IM0、MADL/混在RST、工程10のタイミングと最終検証は残る。現行入口はREADMEとRESTART_R17.md、verify_r17.pyです。

# 現行：restart R16

R15.3は実機回帰・SofaRun/スペースマンボウPLAYまで確認済み。工程9のLDH（HL間接ペア転送）を追加し、EX(SP)のワークレジスタと加算器を共用。既存EZ80LDH P2:PASSを期待。残るNOT READYはLDXの1本。R16のGOWIN/実機、規模、タイミング収束は未確認。現行の入口はREADMEとRESTART_R16.mdです。

# R15.3 現在の状況

R15でEZ80CT1 Stage Vの不一致、R14で同一COM PASSを確認。今回、TSTをEDデコード内へ統合する回帰比較版を作成。機能はR15と同一で、実機回帰解消は未確認。工程9のLDH/LDX、工程8の残項目、工程10のタイミング/規模/最終実機確認は未完了。

# R15 現在の進捗

工程9のTST（レジスタ／即値／メモリ）を追加。既存AND演算器を共用。通常版R14を採用し、LUTが189増えたR14.1は不採用。COM20本は同一。EZ80TST /RUNはP2:PASSを期待し、残るNOT READYはLDH／LDXの2本。工程8の残項目と工程10のタイミング・最終実機検証も未完了。

# R14時点の更新

R13.1はユーザー実機合格。GOWIN成功・Logic90%、MEM／MAD／実装済みRUNALL PASS、SofaRunからスペースマンボウの起動・プレイを確認。R13のMEM FAILとMADLフリーズは同じ試験範囲で再現しなかった。根本原因の確定とSTA達成の証明ではない。

現在は大工程8。R14で4形式の混在CALL／RET.L、条件分岐を追加し、既存MADLフレームFSM・ワーク・カウンタを共用する。フレーム用SPS／SPL増減を1本の24bit加算回路に集約。状態数と24bitワークは増やさず、追加制御2bit。R14のGOWIN・Logic・STA・実機は未確認。

COM20本はR13.1と同一でFLASH更新不要。今回からEZ80MIX /RUNはP2: PASSが期待値。残るNOT READYはLDH／LDX／TSTの3本。まずMEM、その後MIX、MAD、RUNALL、SofaRunを確認する。混在／MADL RST、ADL IM0、工程9残命令と工程10最終検証は未完了。現行はREADMEとRESTART_R14.mdを優先し、以下は履歴。

# R13.1時点の更新

R13はGOWIN合成成功・Logic89%だが実機不合格。EZ80MEMがStage1 FAIL（ソース上07FFFE、EXP31／ACT33）、EZ80MADは電源再投入後も単独フリーズ。工程8のMADLを実機合格にしない。

R13.1は通常／MADLのCPUバス出力レジスタ共用による修正候補。新命令は追加しない。GOWIN・実機は未確認で、根本原因確定／不具合解消とは扱わない。COM20本はR13と同一。まずMEM、その後MADL、RUNALL、SofaRunを確認する。詳細はREADMEとR13_HARDWARE_FAILURE_AUDIT.mdを優先する。タイミング例外は追加しない。

工程1〜6の既存実機結果、工程7のネイティブ割り込みの既存実機結果は履歴として維持するが、R13.1全体の回帰確認は必要。工程8の残り（混在CALL／RET等）、ADL IM0、工程9の残命令、工程10のタイミング・最終検証も未完了。

以下は履歴。

# R13時点の更新

現在は大工程8。R12のMBASEはユーザー実機でPASS（GOWIN成功、Logic86%、EZ80MEMと実装済みRUNALLはPASS、SofaRunスペースマンボウ起動・プレイ）。R13はMADL、IM1／IM2／NMIのモード付きSPLフレームとRETI.L／RETN.Lを実装・シミュレーション検証した。R13のGOWIN・規模・タイミング・実機は未確認。

EZ80MAD.COMのみDI／IM1起動シムへ更新し、FLASH書換えが必要。EZ80MAD /RUNはP2: PASSが期待値。残るNOT READYはLDH／LDX／MIX／TSTの4本。混在CALL／RETは次段階で、MADL IM0／MADL RSTも未対応。工程8全体の完了とは扱わない。

| 工程 | 現在の状態 |
|---|---|
| 1〜6 | ユーザー実機合格済み。既存回帰を継続 |
| 7 | MADL=0のIM1／IM2／NMI・RETI／RETNは実機確認済み。ADL IM0は残項目 |
| 8 | MBASEはR12実機合格。R13 MADL割り込みフレームの実機確認待ち。混在CALL／RET等は残項目 |
| 9 | MLT、LEA／PEA、I16等は対応済み。LDH／LDX／TST等の残命令を実装・検証する |
| 10 | 回帰を継続。GOWINのSetup／Hold未達と最終実機検証が残る |

現行はREADMEとRESTART_R13.mdを優先する。以下は履歴。

# R12時点の更新

工程8のMBASEを実装。既存EZ80MB /RUNはP2: PASSを期待する。残るNOT READYはLDH／LDX／MAD／MIX／TSTの5本。MADLと混在フレームは未実装。工程7のネイティブADL IM0、工程9残命令、工程10の最終タイミング・実機確認も残る。

R11.10はユーザー実機PASSだがSTA未達。R12は同版を基準に命令追加へ戻した。回帰を実施し、GOWIN／実機は未確認。以下は旧版の履歴で、現行は本節とREADME、RESTART_R12.mdを優先する。

# R11.10時点の更新

R11.9はGOWIN成功・Logic86%、実機EZ80MEMと実装済みRUNALLはPASS、6本NOT READY、SofaRunからスペースマンボウの起動とプレイを確認済み。ただしSTA未達。R11.10はCPU Upper通常書込みを共通化する候補で、新命令は追加せず、GOWIN／実機は未確認。

現在は工程10のタイミング対処と回帰を先行中。工程7のADL IM0、工程8のMBASE／MADL／混在フレーム、工程9の残命令、工程10の最終確認が残る。以下の旧版記録は履歴であり、現状は本節とREADMEを優先する。

# R11.9時点の更新

R11.8はユーザー実機でEZ80MEM、実装済みRUNALL、SofaRunからスペースマンボウの起動・プレイを確認済み。ただしLogic87%、54MHz系Fmax31.809MHz、Setup477／Hold42端点で全体改善とは判断しない。

R11.9はCPUをR11.7へ揃え、SD制御レジスタの読出し番号を既存選択段で保持する候補。R11.7とのFPGA差分はtopのSD読出しだけ。GOWIN／実機は未確認。工程10のタイミング・回帰を先行中。ネイティブADL IM0、工程8のMBASE／MADL／混在復帰フレーム、工程9の残命令は未完了。

以下は過去の記録。

# R11.7時点の更新

R11.6はユーザー実機でEZ80MEM、RUNALLの実装済み項目、SofaRunからのスペースマンボウ起動・プレイを確認済み。Logicは86%（87%から訂正）。impl(6).zipでSetup490／Hold42端点、54MHz系Fmax37.732MHz。機能回帰は通るがタイミング達成には至っていない。

R11.7はIRと同時保持する8bitのWrite分類を追加し、追加命令のWriteデコードを専用回路へ分離する。新命令の追加なし。工程7のネイティブADL IM1／IM2／NMIとRETI／RETNは実機確認済み。ネイティブADL IM0、工程8のMBASE／MADL／混在復帰フレーム、工程9の残命令は未完了。工程10のタイミング・回帰を先行中で、R11.7のGOWIN・実機は未確認。

以下は過去の工程記録。

# R11.6時点の更新

R11.5はGOWIN合成成功・Logic87%。ユーザー実機でEZ80MEM PASS、RUNALLは実装済み項目PASS（LDH／LDX／MAD／MB／MIX／TSTの6本NOT READY）、SofaRunからスペースマンボウの起動とプレイを確認。

R11.6は要求保持後のベクタ選択をT1の捕捉へ移すタイミング改善候補。新命令の追加なし。GOWIN／実機は未確認。詳細はTIMING_R11_6.mdとプロジェクトREADME.md。工程7のネイティブADL IM1／IM2／NMIとRETI／RETNは実機確認済み（ネイティブADL IM0は未実装）。工程10のタイミング作業を先行している。工程8と工程9の残項目、工程10の最終確認は未完了。

以下は過去の工程記録です。

## R11.5時点の追記

基準はR11.4B。GOWIN合成、EZ80MEM、RUNALL実装済み全PASS、SofaRunからスペースマンボウの実機プレイを確認した。
R11.5は工程10のタイミング対処を先行する修正版。診断ベクタ窓を保持済み要求で選択し、SDRAM要求にも下降サンプルを追加する。16/24bit分離とMSX側遮断を維持する。
R11.5自体のGOWINと実機は未確認。詳細はTIMING_R11_5.md。以下は過去の工程記録を含む。

## R11.3 時点の追記

R11.2はGOWIN Logic86%、実機EZ80MEMとRUNALL対応済み全PASS、未実装6本NOT READY、SofaRunゲームプレイを確認した。
R11.3は工程10のタイミング対処を先行する修正版。要求時のMSX遮断保持、命令分類の拡張、SDRAMの下降エッジ捕捉を変更した。
工程8のMBASE／MADL／混在フレームは未着手、ADL IM0も未実装。R11.3自体のGOWIN／実機は未確認。
下記は過去の工程記録を含む。現行の実装・検証条件はREADMEおよびTIMING_R11_3.mdを参照する。

# 大工程の進捗（ユーザー提示の10工程に統一）

過去のR7／R8説明にあった「4番目」「5番目」はR3完了後からの独自の数え方であり、本表の工程番号ではない。以後は以下の番号を使用する。

| 工程 | 内容 | R11.2時点の状態 |
|---|---|---|
| 1 | R3の実機確認：交換・SP転送・複数バイトアクセス | R3で実機合格 |
| 2 | データアクセスの残り：24bit絶対バイトアクセス、EX(SP)など | R4で実機合格 |
| 3 | 24bit演算：ADD／ADC／SBCとフラグ | R5で実機合格 |
| 4 | ブロック転送・比較命令の24bit対応 | R6で実機合格 |
| 5 | ADL状態と24bit命令フェッチ、PC境界処理 | R9でGOWIN合成・実機PASS、LUT84% |
| 6 | 24bit JP／JR／CALL／RET／RST | R10でGOWIN合成・CTL／ADL／F9実機PASS、LUT85%。混在フレームは工程8 |
| 7 | ADL割り込み・NMI・RETI／RETN | R11でMADL=0のIM1／IM2／NMI・RETI／RETNを実装・機能検証。R11でGOWIN・IRQ／IM2／NMI実機PASS、Logic87%。ADL IM0は残課題 |
| 8 | Z80／ADL混在、MBASE・MADL・復帰フレーム | 基本JP往復は対応。MBASE／MADLと混在CALL／RETフレームは未実装 |
| 9 | 残るeZ80追加命令と命令別の検証 | 一部先行完了。R7のMLT、R8のLEA／PEAは実機合格。R11でIM2に必要な16bit I転送を先行 |
| 10 | 全体回帰、GOWINタイミング・規模確認、実機最終検証 | R11.1で合成・ゲーム動作確認、STA未達。R11.2で命令分類・EX(SP)ワーク・SDRAM捕捉を改善。新GOWIN／実機待ち |

R8のGOWIN合成成功、EZ80LEA P1: PASS、SofaRunからのスペースマンボウ起動・プレイを、R9の基準となるユーザー実機報告として記録する。
R9のGOWIN成功・LUT84%・EZ80F9 R9: PASS・SofaRunからスペースマンボウのプレイを実機報告として反映。工程5は実機合格。R10の工程6実機合格（CTL／ADL／F9、GOWIN、LUT85%、SofaRunからスペースマンボウのプレイ）を反映。R11は工程7。工程8〜10、ADL IM0等の残項目が残る。
工程9は、I/Oポート上位00h固定の追加命令を除外するユーザー方針を反映する。
