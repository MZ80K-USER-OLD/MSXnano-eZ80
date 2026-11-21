# R24 命令取得時に実行制御を確定する

## 基準と目的

基準はR23.3。ユーザー実機でEZ80MEM、EZ80MR4、EZ80ION、RUNALLがPASSし、SOFARUNからスペースマンボウの起動・PLAYが確認されている。Logic報告値95%。R24の実機確認は未実施。

従来の実行制御は、保持したopcodeクラスに加え、ページ・ADL・幅指定・DD/FD状態を組み合わせ直していた。R24は `Decode_Execution` にこの命令固有判定を集め、本命opcodeを受理した時点で `Exec_Control` に保持する。マイクロコードとCPU本体は保持した有効条件を参照する。

## 捕捉タイミング

| タイミング | 保持する情報・動作 |
| --- | --- |
| リセット | Z80互換モード、制御語ゼロ |
| 通常M1/T2、ClkEn=1、WAIT_n=1 | 次のopcode・ページ・DD/FD選択・データ幅・ストリーム幅・明示幅指定を変数で確定し、IRと制御語を同時更新 |
| 幅プレフィクス取得 | 幅指定を保留。後続の本命opcodeでADLの既定幅と合わせて決定 |
| DD/FD CB | CB取得時に幅を消費し、アドレス計算に渡す。最終opcodeはM7/T2で受理し制御語を更新 |
| WAIT中／CPU停止中 | opcodeと制御語を保持 |
| 混在フレーム完了 | IRをNOPにし、それに対応した制御語へ更新して次の取得へ進む |

信号代入の旧値を誤用しないよう、Dec_Op／Dec_Page／Dec_XY／Dec_Data／Dec_Stream／Dec_Hasの次状態変数からIRと制御語を生成する。40h=16/16、49h=24/16、52h=16/24、5Bh=24/24（データ／命令ストリーム）。8bitデータ処理自体は従来どおり。

通常CB／EDページ内ではDDh・FDh・EDh・CBhも本命opcodeとして幅指定を消費する。値がプレフィクスに見えるため次命令に幅が残る問題を修正した。旧版で再現し、修正版でZ80/ADL×4幅×4終端opcode×通常/WAIT・CE停止の64ケースを確認する。

## 制御語

50bitのexec_control_tを使用する。旧Opcode_Class 16bit FFは削除した。ソース上は差引34bit増だが、重複・未使用ビットの最適化後FF数とLUT数はGOWINの結果で判断する。

| bit | 定数（EC_を省略） |
| --- | --- |
| 0 | EX_SP |
| 1 | STACK |
| 2 | INCDEC |
| 3 | BYTE_ABS |
| 4 | PAIR_ABS |
| 5 | PAIR_IND |
| 6 | ARITH |
| 7 | PAIR_INDEX |
| 8 | BLOCK |
| 9 | MUL |
| 10 | EA |
| 11 | PEA |
| 12 | JP |
| 13 | NATIVE_CTRL |
| 14 | IRQ_RETURN |
| 15 | IV_READ |
| 16 | TST |
| 17 | IO2 |
| 18 | SP_READ |
| 19 | EXT_MODE0 |
| 20 | WIDTH_PREFIX |
| 21 | IMM_LONG |
| 22 | ADL_ED_ALIAS |
| 23 | MIX_CTRL |
| 24 | MIX_SUPPORTED |
| 25 | IV_PAIR |
| 26 | MB_OPCODE |
| 27 | MADL_OPCODE |
| 28 | MIX_IRQ_RETURN |
| 29 | EXT_BASE |
| 30 | ANY_LONG |
| 31 | ED_NO_WRITE |
| 32 | EXT |
| 33 | FRAME_CALL |
| 34 | FRAME_RET |
| 35 | FRAME_IRQ_RET |
| 36 | FRAME_RST |
| 37 | RST_WIDTH_OK |
| 38 | RST_WIDTH_BAD |
| 39 | DATA_LONG |
| 40 | MB_VALID |
| 41 | IV_WRITE |
| 42 | EXPLICIT_WIDTH |
| 43 | ADL_SNAPSHOT |
| 44 | CALL_KIND |
| 45 | RET_KIND |
| 46 | RST_KIND |
| 47 | UNCOND_FLOW |
| 48 | JP_ALWAYS |
| 49 | RETN_OPCODE |

IO2のビット名は既存制御との互換性のため残るが、削除済みINI2等の実行は復活させない。ED命令のデコードはEDページ内を維持する。

t80_mcode_ez80.vhdの通常命令の複合ガードは保持済み制御語を使う。旧インターフェースExt_Active／ADL_Mode／Has_Widthは互換性のため残し、保持済みスナップショットへ接続している。これらを通常命令の複合if条件に再使用しない。

## 実行時に残す判定

MCycle/TState、WAIT、CEN、IRQ/NMI受付、条件フラグによる分岐、割込みフレームの進行は実行中に変化するので残す。PC取得幅や割込み受付時のADL、復帰によるADL変更はアーキテクチャ状態として扱う。通常opcodeのページ別制御表、operandフィールド選択、ALUのサイクル別動作も維持する。全制御をFFだけの制御列へ展開する変更ではない。

## メモリとタイミング

R23.3のez80_memory_bridge.v、SDRAMコントローラ、top、GPRJ、制約は変更しない。16bit MSXバスと24bit拡張バスの分離、拡張アクセスでMSX側FFFFhのセカンダリスロットレジスタを誤アクセスしない遮断を維持する。

期待する経路分割は「取得opcode・ページ・幅状態 → 命令固有判定 → Exec_Control FF」と「Exec_Control FF → MCycle/TState等の実行選択 → 制御先FF」。取得側の新しいFF入力経路も確認が必要であり、段数・LUT・Fmaxの改善は未確定。FFを増やすだけで回路規模が必ず減るわけではない。

R23.3レポートでは54MHz領域のFmaxが32.633MHzでSetup違反が残る。CPU側表示Path1はIR[1]からRD系CEまで、slack −6.063ns。表示400経路中の最小はVRAM→sprite CEの−6.944nsであり、CPU経路だけ直して全体のタイミングが閉じるとは限らない。R24では同一制約で新旧レポートを比較し、Exec_ControlのD側／Q側、Request_Extended保持FFまで、VRAM、Hold違反を確認する。一律のマルチサイクル・False Path追加はしていない。

## 検証と実機テスト

新旧マイクロコードの全出力を4モード、各458752入力、合計1835008入力で比較する。これは制御表の比較であり、命令列の時系列検証とは別。時系列検証ではメモリ実COM、混在CALL/RET/RST、MADL、MBASE、LDH/LDX、幅プレフィクス、IM0を実行する。結果・対象ソースのSHA256はverification_r24参照。

新規hardware_test/EZ80DEC.COMは16ケース：Z80/ADL×4幅×CB DDh/FDh。直後の無指定LD DE,nnの長さ・レジスタ・スタックを確認する。旧版では新しい診断IDがないためNOT READY。診断セッションを有効化してE0h=24h、E1h=DBhを読む。既存COMは変更しない。

MSX-DOS表示はZ80モード・MBASE=0・拡張ロック状態で行い、BDOSがEIする前提で呼出直後にDIする。拡張領域テスト中は割込みを無条件に許可しない。FAIL表示にStage／ADDR／EXP／ACTを含める。シミュレーションではBDOS側EIと実IRQ受付も確認する。

実機順序はREADMEに従い、EZ80MEMを最初に単独実行。期待表示EZ80DEC R24: PASS、CRC32 39161D22。GOWIN・実機はユーザー環境での確認待ち。
