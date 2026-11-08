# R14 混在CALL／RETとLUT抑制の共用方針

## 基準と変更範囲

実機合格済みR13.1（GOWIN成功、Logic90%、MEM／MAD／実装済みRUNALL PASS、SofaRunスペースマンボウ起動・プレイ）から開始する。R14のGOWIN／規模／STA／実機は未確認。FPGA変更はt80_ez80.vhd、t80_mcode_ez80.vhd、g80a_ez80.vhdの3ファイルだけ。packのインタフェース、外部ポート、top、GPRJ／CST／SDC、ブリッジ、SDRAM、VDPは同一。

元ソースはr13_1_mixed_baseline、差分はR14_MIXED.patch、再適用入口はtools/extend_mixed_r14.py。COM20本とBATはR13.1と同一で、FLASHの更新は不要。EZ80MIX.COMのCRC32=5063B89A、3123bytes。

## CALLの4形式

| 起点 | プレフィクス | 戻りPCの保存先 | SPLのモード | 呼出し先 |
|---|---|---|---|---|
| Z80 |40 .SIS|中位→下位をMBASE:SPS|02|MBASE:即値16|
| Z80 |52 .SIL|中位→下位をSPL|02|即値24・ADL|
| ADL |49 .LIS|中位→下位をMBASE:SPS、上位をSPL|03|MBASE:即値16・Z80|
| ADL |5B .LIL|上位→中位→下位をSPL|03|即値24・ADL|

各スタックは保存前に減算する。SPSは16bitでラップし、上位はMBASE。SPLは24bitでラップする。モードバイトが最終SPLを指す。MBASE自体はフレームへ保存しないため、calleeがMBASEを変える場合はソフト側で元に戻す必要がある。

RET.LIS（49）はSPLのモードを読み、03ならPC上位をSPLから、PC下位2バイトをMBASE:SPSから読む。RET.LIL（5B）はモードとPC2／3バイトをSPLから読む。戻りモード02ではPC上位を0にし、Z80フェッチにMBASEを使用する。03ではPC24を復元する。R13のRETI.L／RETN.Lと同じ読出し処理を使用するが、通常RET.LではIEF2をIEF1へコピーしない。

条件付きCALLは成立しなくても即値を読み終えて次の命令へ進み、スタックとモードを変更しない。条件付きRET.Lは不成立ならモードバイトも読まず、SPを進めない。成立条件は従来の保持済みBranch_Conditionを使う。A／Fは変更しない。

表の4形式とRET.Lを対象とし、CALLのData_Longが現在ADLと異なる表外形式、短いサフィックス付きRET、サフィックス付きRSTとMADL RSTは今回有効にしない。これは今回の対応範囲であり、Zilogの全サフィックス仕様を実装済みとする主張ではない。通常のサフィックスなしCALL／RET／RSTと、MADL=0ネイティブADL割り込みは維持する。

## 共用による規模抑制

| 対象 | R14での扱い |
|---|---|
| フレームFSM |既存8状態のまま。ベクタ読出し状態をCALL即値の読出しにも使う|
| 24bit目標／戻りPC |既存Ctrl_Target／Ctrl_Returnを共用。新規24bitワークなし|
| 即値フェッチ |既存PC／PC_Incrementを共用。CALL専用アドレスカウンタなし|
| バイトカウンタ |既存Frame_Countを共用。追加カウンタなし|
| スタック増減 |SPS16／SPL24のプッシュ・ポップを1本の24bit加算回路へ集約|
| モード |既存Frame_Mode_BitとStream_Longを共用。呼出し先モード専用FFなし|
| 命令分類 |既存Write_ClassのA/B（CALL）とC/D（RET）を共用。IR全体からの重複分類を避ける|
| バス出力 |R13.1のAddress_Reg／Address_Bank_Reg／Data_Out_Regを継続使用|
| WAIT／CEN／BUSRQ |既存エンジンの停止・保持・バス要求保留を共用|
| 追加制御FF |Frame_Is_CallとFrame_SPSの2bit|
| BSRAM／乗算器 |追加なし|

Frame_Stack_ValueでSPS／SPLを選び、Frame_Stack_Deltaで+1／-1を選び、Frame_Stack_Nextで加算する。SPSの場合は結果の下位16bitだけを採用し、アドレス上位はMBASEを使う。SPSのPC2バイト保存が終わった時は、同じ増減器をSPLへ切り替え、必要なPC上位とモードを保存する。

これらはRTL構造上の共用を確認した結果。GOWINが割り当てるLUT／ALU／CLSやFmaxの実測ではない。制御用の選択回路も増えるため、Logicが必ず低下するとは主張しない。R14のGOWIN結果でR13.1のLogic90%と比較する。

## 捕捉・保持と割り込み

M1/T4で既存フレームエンジンへ入り、refresh終了のバブルを経て新しいメモリT1を開始する。CALLの即値は呼出し元PC幅で読み進め、全バイトが揃った時に戻りPCを捕捉する。呼出し先の即値長はStream_Longで決める。呼出し元PCが境界を越えた場合も、戻りPCは読出し完了後の値である。

アドレス／データは出力レジスタへ保存し、ラッパは従来のT1下降で要求を保持する。フレームT2はWAIT完了まで停止し、T3で次のバイトのアドレス・データ・ポインタへ進む。CEN停止中は保持し、BUSRQはフレーム完了後に扱う。出力直前へSPL／SP／PCのライブMUXを追加しない。

CALL／RET.Lは割り込み許可状態を保持する。エンジン中のNMIは命令完了まで保留し、CALLが目的モードへ到達してから割り込む。RET中の保留IRQは復帰後のモードで受け付ける。IRQ入口のIEFクリアとRETNのIEF2復元は既存の規則を維持する。ネストしたCALLでもワークレジスタを保存する必要はなく、前の呼出しの戻り情報はすでにメモリのフレームに保存されている。

MSX16と拡張24の分離を維持し、非ゼロバンクではMSX16=0000h／MREQ遮断を維持する。FFFFhのセカンダリスロット判定回路には触れない。プライベート／MegaRAM／VRAMの既存物理配置、VDP優先とCPU WAITも同じ。I/O上位00h固定の追加命令は実装しない。

## 検証

全体548回帰ケース＋故障検出22ケース。R13.1の353ケースから、今回対応した4つの旧停止試験を成功系へ移し、実COMのMIXが1→7条件となり6ケース追加、混在補足192ケースと診断なし実COM1ケースを追加した。故障検出は20→22。旧停止試験の退役は不具合を無視したものではなく、同じ命令をフレーム付き成功試験で検査するための更新である。

混在64シナリオ×3設定（DIV4通常、DIV4ストレス、DIV16ストレス）。起点と目的モード4通り×MBASE00／0E×MADL0／1、8条件のCALL／RET成立・不成立、入れ子、PCの16／24bit境界、SPS／SPLのラップ、CALL中NMI・RET中IRQ、無効モードと表外CALL停止を含む。各フレーム書込みのアドレス・バイト順、復帰時PC／ADL／SP／SPL／A／F／IEFを照合する。WAIT・CEN停止・バス要求を監視する。

補足試験は16MiBフラットRAMによる論理境界試験で、基板の物理配置を表すものではない。実COMは別に実CPU／ブリッジ／SDRAMモデルへ接続する。7条件には位相、WAIT、CEN停止、/RUNなし、拡張無効、故障表示を含む。MIXの故障注入はStageBの030400hを72→73へ壊し、ADDR／EXP／ACTの表示を確認する。診断注入なし構成でもMIXがPASSすることを検査する。

補足の2故障は共有Data_Out_Regのフレーム書込み値破壊と、短いプッシュ段階Frame_SPSの無効化。後者はSPSからSPLへ不正に移るため、書込みアドレス照合で検出する。通常MADLの78ケース＋2故障検出も再実行する。

デコーダはMode0〜3・合計8,388,608入力組。Mode0、Ext=1、HasWidth=1、ISet=base、非割込みのうち、CALL9オペコードでData_Long=ADL、RET9オペコードでData_Long=1の1152組のみを旧版比較から除外し、残り8,387,456組・49出力を比較する。除外した動作は実CPU試験で補う。全内部状態の形式的等価性証明ではない。

通常プログラム6本ではUpper64bit、バス、PC、SPL、Fを実R13.1コアと各クロックで比較する。MBASE試験のC4応答期待値は97→9Fに更新する。GOWIN／実機、全MSX BIOS／DOS、物理遅延はここでは検証していない。

## 診断ABIと仕様参照

混在CALL／RET.Lのbit3を有効にし、マスクは839F／039F。C4=9F、C6=60、C5=83／03、C7=7C／FC。C8=MBASE、C9=MADL。P2版と全COMバイト列は変えない。未準備はLDH／LDX／TSTの3本。

ZiLOG eZ80 CPU User Manual UM007715-0415、Memory Mode SwitchingのCALL（表14）とRET（表18）、条件付きCALL／RETの説明を参照：https://www.zilog.com/docs/um0077.pdf 。独自KC160風M0／M1／M2方式とは混同しない。

混在calleeはRET.Lで戻す。通常RETだけのBIOS／DOSを直接calleeとして置換せず、必要ならZ80側で通常CALLを行ってRET.Lで戻すラッパーを用意する。実機COMは操作途中でDOS／BIOSを呼ばず、Z80・MBASE00・MADL0へ戻してから結果を表示する。DOS／BIOSがEIする可能性も従来どおり考慮する。

工程8の残り（混在／MADL RST等）、ADL IM0、工程9の残命令、工程10のタイミング達成と最終実機確認は残る。新しいタイミング例外や一律の制約緩和は追加しない。
