# R13 MADL割り込みと復帰フレーム

## 基準と変更範囲

基準は実機確認済みR12。FPGA変更はG80A_eZ80内のcore、mcode、pack、wrapperの4ファイルだけ。MADL_Stateをコアからラッパへ内部接続するが、FPGA外部ピンとラッパ外部24ポートは追加しない。元のG80A、top、メモリブリッジ、SDRAM、VDP、GPRJ／CST／SDCは同一。元R12ソースはr12_madl_baseline、差分はR13_MADL.patch、再適用入口はtools/extend_madl_r13.py。

STMIX／RSMIXは拡張有効・Mode0のED 7D／7Eを専用デコードする。既存のED別名RETNやIM変更を抑止し、1マシンサイクルでMADLだけを更新する。無効時は従来T80の別名動作を維持する。MADLはリセット0。ローカル拡張ゲートをZ80で閉じる際はMBASEとともに0へ戻す。

## エンジンの捕捉と転送

要求開始は内部MCycle1／TState4、バス未譲渡時。割り込み入口ではPCと元ADLを捕捉し、Ctrl_Return／Ctrl_Target／IRQ_Vectorの既存ワークを共用する。通常CPUのClkEn、通常レジスタ書込みを停止するが、割り込み入力同期はCENで継続する。元M1のrefresh終了をT4のバブルで待ち、新しいバイトのT1を出す。ラッパが要求時に保持する24bitアドレス、遮断済みMSX16、拡張判定、書込みデータの契約は従来どおり。

T1→T2→T3の各バイトを実行する。T2はWait_n=1まで保持し、T3で読出し値を消費／ポインタを更新する。CEN=0ではエンジン状態、SP、PC、A／Fを保持。処理中のBUSRQは保留し、通常CPU再開後に譲渡する。フレーム処理中にBUSAKを出さないことを試験する。

完了時にはPC／ADL／アドレスを反映し、内部MCycle1／TState1へ戻す。IR／ISet／幅保留／通常書込みパイプラインをクリアする。これを省くとRETN.Lのデコードが次のM1/T2にも残り、戻り先のPCが進まないため、NMIがIRQフレーム保存中に到着する回帰を追加した。

## 保存と復帰

MADL=1の割り込みはSPLだけを入口で使う。降順にPC上位（元ADL=1のみ）、PC中位、PC下位、02hまたは03hを保存する。最終SPLはモードバイトを指す。IM1=000038h、NMI=000066h。IM2はI16とIACKデータのベクタアドレスから連続3バイトを読み、ADL=1で移る。通常I/O／IACK／refreshのバンク00とMSX16遮断も監視する。

| 復帰形式 | SPLから読むもの | SPSから読むもの |
|---|---|---|
| 5B ED 4D／45（.LIL）、戻りZ80 | 02、PC下位、中位 | なし |
| 5B ED 4D／45（.LIL）、戻りADL | 03、PC下位、中位、上位 | なし |
| 49 ED 4D／45（.LIS）、戻りZ80 | 02 | PC下位、中位 |
| 49 ED 4D／45（.LIS）、戻りADL | 03、PC上位 | PC下位、中位 |

SPLは24bitで、SPSは16bitでラップする。SPS読出しはMBASEを使う。Z80復帰のPCは16bit、フェッチの上位はMBASE。ADL復帰ではPC24を使う。モードバイトが02／03以外ならエンジンを停止し、不正なSPを進めない。

NMIはIEF1をIEF2へ保存しIEF1を0にする。RETNはIEF2をIEF1へ戻す。IRQは両方を0にし、RETIは復元しない。フレーム処理中のNMIは完了境界で承認し、RETN完了境界の保留IRQは復元IEF1とIM1／IM2に従って受け付ける。EI直後の1命令は従来どおり完了させる。

## 実機用COMの変更

EZ80MAD.COMの旧版3066bytesは先頭がDD E5 FD E5 F3で、最初のZ80 IRQ前のIM1指定が不足していた。R13は先頭をJP0CFAh／NOP／NOPへ変更し、末尾へDI／IM1／旧先頭のIX・IY保存／JP0105hの10bytesを追加した3076bytes。旧5bytes以降の全コード・文字列・ADLペイロードのアドレスは保持する。

SHA256は559dcccbc5f2d38412e730cf6b362ae0aae1713c0e2627936c1334cd1f43c4c7。他19COMとBATは同一。旧バイナリと旧SHA一覧を保存し、tools/update_mad_com_r13.pyで差分を再検証する。ASM／hex／vh／JSONも同期する。DOS／BIOSコールはモード操作中には行わず、復帰後に結果を出す。メモリ故障表示はADDR／EXP／ACTを含む。

## 検証範囲

全体353回帰ケース＋20期待失敗。MADLの26シナリオをDIV4通常、DIV4ストレス、DIV16ストレスの3条件で実行し78ケース。ストレスではWAIT、CEN停止、位相ずれ、バス要求を入れる。全256フラグ×両モード×STMIX／RSMIXの1024チェック、IM1／IM2／NMIとMBASE00／0E、両復帰形式、SPL=FFFFFF／000000とSPS=FFFF／0000境界、NMI保留とRETN直後IRQを含む。故障注入はフレーム書込みデータ破壊とRETNのIEF復元無効化の2件。

補足の16MiBフラットRAMはコアの論理境界試験で、基板の物理配置ではない。実COMは別試験で実ブリッジ／SDRAMモデルへ接続する。既存EZ80MEMは07FFFFh／080000h境界とMSXスロット漏れ回帰を含む。VDP優先・CPU WAITの既存回路を変更していない。

デコーダ比較はR12を基準にMode0〜3の合計8,388,608入力組を走査。新規ED7D／7EのMode0・Ext_Active=1・ISet=ED・非割込み512組だけを除外し、残る8,388,096組の49出力を比較する。除外分は実CPU命令試験で補う。全内部状態の形式的証明ではない。Upper64bit／外部バス／PC／SPL／Fは、MADL=0・MBASE=0の6プログラムで実R12コアと各クロックで比較する。

実行入口はtools/verify_r13.py。--reuse-write／--reuse-r3／--reuse-madlは同一作業内で先行実行済みのソースSHAを照合して再利用するオプションで、既定は全試験を実行する。GOWIN、全MSX BIOS／DOS、実機はここでは実行していない。

## 仕様参照と残項目

ZiLOG eZ80 CPU User Manual UM007715-0415、Memory Modes、Mixed-Memory Mode Interrupts、STMIX／RSMIX、RETI／RETNとIEF1／IEF2の説明を参照：https://www.zilog.com/docs/um0077.pdf 。CPUの仕様と、MSX用の拡張ゲートや診断窓のローカル契約は区別する。

今回の機能ビット8はMADL割り込みフレーム用。混在CALL／RETはbit3を立てず、EZ80MIXはNOT READYを維持。MADL=1のRSTは未対応として停止し、IM0は受け付けない。短い割り込み復帰も今回の.L形式とは別で未対応。これらをMADL=0の従来動作へ黙って置換しない。工程8の残り、ADL IM0、工程9ロード／TST、工程10のタイミング達成と実機最終確認を残す。
