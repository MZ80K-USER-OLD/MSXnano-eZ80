# R11：大工程7・通常ADL割り込み

## 基準と範囲

ユーザー実機報告：R10のGOWIN合成成功、LUT85%、EZ80CTL R10: PASS、EZ80ADL P1: PASS、EZ80F9 R9: PASS、その後SofaRunからスペースマンボウをプレイできた。
これを工程6の通常ADL制御フローの実機合格として記録する。

R11はMADL=0のADL IM1／IM2／NMIと、無指定のRETI／RETNを実装する。IM2のため16bit IとLD I,HL／LD HL,Iも先行実装する。
リセットはADL=0・拡張ロックのまま。通常Z80のSPSは16bit、ADLのSPLとPCは24bit。
R11はユーザー報告でGOWIN合成成功、Logic87%、IRQ／IM2／NMI P2: PASS、SofaRunからスペースマンボウのプレイを確認済み。STA違反は残る。最新のタイミング改善はTIMING_R11_1.mdを参照。

| 項目 | R11 |
|---|---|
| 通常ADL IM1 | 24bit SPLへ3バイト復帰PC、000038hへ移行 |
| 通常ADL IM2 | 16bit IとIACKの下位8bitから表アドレス。表から3バイトISR先を読み、PC24へ反映 |
| 通常ADL NMI | IEF2へ実効IEF1を保存、IEF1を解除、SPLへ3バイト復帰PC、000066hへ移行 |
| 無指定ADL RETI | SPLから3バイトPCを復帰。ISR側でEIしなければ割り込み許可を勝手に再設定しない |
| 無指定ADL RETN | SPLから3バイトPCを復帰し、IEF1をIEF2から復元。復元後の保留IRQを同じ命令境界で判断 |
| EI／HALT | 次の1命令までIRQを待ち、HALTからIRQ／NMIで復帰 |
| NMI優先／保留 | 同時のIRQよりNMI優先。ADL受付中の次のNMIエッジを保留する |
| 16bit I | LD I,HL／LD HL,I。LD I,AはI下位8bitだけ更新。HLへの転送は下位16bit、上位8bitを保持 |
| 未対応 | ADL IM0、MADL=1、混在CALL／RET.L／RETI.L／RETN.L、MBASE。これらは別工程に残す |

ADL IM0ではIRQの受付を抑止する。IM0をIM1へ読み替えない。ADLでIRQを使う前にIM1またはIM2を設定する。
ADLで割り込みを利用する前に、SPLをマップされたプライベートRAMへ初期化する。リセット値FFFFFFhはこの基板の有効スタック領域ではない。
Z80の従来IM0／IM1／IM2経路は維持する。元G80Aソースは変更しない。
MADL付きのフレームは工程8。プレフィクス付きRETI／RETNを通常3バイトフレームとして解釈せず、停止保護する。
ED75hの従来RETN別名もADLでは停止し、16bit SPSへの誤った復帰を防ぐ。未実装オペコード全体を例外化する仕組みではない。
上位00h固定の追加I/O命令は引き続き実装しない。

## 受付・捕捉・保持

IRQ／NMIは命令またはブロック反復のバイト境界で受ける。幅指定やED／DD／FDなどのプレフィクスの途中では受けない。
WAITを受けている読書きサイクルを途中で切らず、完了後の境界で判断する。ブロック継続時の保存PCは幅プレフィクスを含む再開位置。
CEN停止中は状態・SPL・出力を進めない。立上り／立下り許可を1 T-state全体として対にした試験条件を使う。

受付M1で復帰PCを既存の保持レジスタへ捕捉する。書込み順はSPL-1に上位、SPL-2に中位、SPL-3に下位。DOは各書込みT1で登録し、WAIT中はアドレス・データ・SPLを保持する。
復帰は下位・中位・上位を順に読み、最後のバイトを受けた時点でPC／アドレス上位を反映する。
IM2はIACKのバイトを捕捉して24bit表ポインタを保持し、3回の読出しを行う。表ポインタの更新はWAIT解除後に1回だけ行い、64KiB境界をまたいでも上位を失わない。

EIの内部IFF更新が次フェッチ側にあるT80の構造に合わせ、ADLでEI終了境界にNMIが来た場合はEI後の実効状態を保存する。
受付M1に残る直前命令のEI／DI制御を抑止し、NMI受付直後にIEF1が誤って再設定されないようにする。
NMI保留の解除は実際の受付境界に合わせ、同じクロックに新しい立下りエッジがあれば新しい要求を残す。保留は1件で、多数のエッジを数えるFIFOではない。多重NMIの各層のIFFを保存するハードスタックは持たず、必要な場合はISR側の保存が必要。

原版からの拡張で注意する箇所は `T80_EXTENSION_NOTES.md` に整理する。
機能モデルの合格は、GOWINのsetup／hold成立を意味しない。追加のfalse_path／一律multicycle緩和は行っていない。
SDC／CST、SDRAM制御、メモリブリッジ、VDP優先仲裁とCPU WAITはR10と同一。

## 先行配布P2との接続

P2のCOMはバイト単位で変更しない。E7E7hの署名・機能照会を実装する。
対応マスクは診断接続あり8287h、なし0287h。bit0=IM1、bit1=IM2、bit2=NMI、bit7=I16、bit9=RST、bit15=診断入力・ベクタ接続。
MBASE／MADLはまだ保持レジスタを持たず00相当のため、C8／C9は00を返す。対応していない機能のビットは立てない。
A5h→5Ahの開放直後は従来どおりE1hを返し、古いCOMの判定も維持する。

CPUラッパーのDIAGNOSTICS既定値はfalse。対象GPRJのtop_ez80は明示的にtrueにし、同じGPRJで診断テストを使えるようにする。
診断回路はリセット時に無効。D8を受けるまで通常のINTとアドレス接続を維持する。

- D8中だけ通常VDP等のINTをCPUへ渡さず、試験IRQ／NMIをINT_n／NMI_nの受付経路へ接続する。
- D1で試験IRQを保持。D2はHALT後に8 CPU許可クロックのNMI低パルスを1回生成する。CPUの内側の保留フラグを直接変更しない。
- D8中の000000h〜00007Fhの読出しは、論理0F0000h〜0F007FhのプライベートSDRAMへ変換する。JPの即値読出しも含む。MSX BIOS ROMを書き換えない。
- CPUラッパーでMREQ/T1より前の読出し意図を使って変換する。既存ブリッジは通常の高位要求としてWAITと要求捕捉を行い、MSX側を遮断する。
- IACKのFEhはM1のIACKだけへ供給する。後続のスタックやIM2表読出しへFEhを上書きしない。
- D4は試験要求を解除し、通常INTのマスクとベクタ接続を維持。D0／拡張ロック／リセットで通常接続へ戻す。

通常VDPの表示・SDRAM仲裁は続く。外部の新しいピンや新しいI/Oアドレスは増やさない。
外部物理NMIピンの接続や非同期入力の短パルス／メタステーブル性を実機検証したものではない。今回のNMIはラッパーが同一クロック系から入力へ与える試験パルス。

## 実機手順

1. ZIPを短いパスの新規フォルダへ完全展開する。
2. `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をGOWINで全ビルドする。
3. R10で成功したDual Purpose Pin設定を維持する。付属build.tclの値はSSPI／MSPI as GPIO有効、SystemVerilog 2017。GPRJにはIDE全体のオプション値が列挙されていないためIDE側も確認する。
4. 配置配線後タイミングとLUT使用率を記録し、R11を書き込む。
5. 先行配布P2のCOMをそのまま実行する。

```
EZ80IRQ /RUN
EZ80IM2 /RUN
EZ80NMI /RUN
```

期待表示はそれぞれ `EZ80IRQ P2: PASS`、`EZ80IM2 P2: PASS`、`EZ80NMI P2: PASS`。
R11の同梱GPRJでは、これらのNOT READYは合格ではない。ビットストリームの版とDIAGNOSTICS設定を確認する。
追加の確認は `EZ80I16 /RUN`、`EZ80RST /RUN`。期待表示は同じくP2: PASS。
R10までの `EZ80CTL /RUN`、`EZ80ADL /RUN`、`EZ80F9 /RUN` も回帰する。
P2のMIX／MB／MAD／TST／LDH／LDXはまだNOT READYが正常。

終了後はSofaRunからスペースマンボウを起動してプレイを確認する。
ADLの実ISRをZ80専用のMSX BIOSへ直接流さない。P2は試験時だけ専用ADL ISRへ切り替え、Z80／通常接続へ復帰してからDOSを呼ぶ。
DOS／BIOSがEIすることを前提に、テスト中の出力は最後まで保留する。メモリ不一致はADDR／EXP／ACTを表示する。
P2のJSONは先行配布時の仕様と未検証表示をそのまま残す。現在のCPU対応・検証結果は本書と本版のverification_result.jsonを優先する。

## 検証範囲

最新の件数・対象ハッシュはverification_result.json、ログはverification_logsに収録する。

- R3〜R10の互換回帰を再実行。R9のRETI／RETN停止を期待する旧2ケースは対応開始に伴い廃止し、実動作と未対応サフィックスの試験へ置き換える。
- 実際のP2 COMをCPU・ブリッジ・SDRAM制御・SDRAMモデルで実行。位相、WAIT、CEN停止、高速側分周、結果破損、引数なし、拡張無効、未対応機能を検証する。
- CPU単体で、LDIRの幅プレフィクスが64KiB境界をまたぐ再開、最初のバイト書込みのWAIT中のIRQ／NMI、NMI優先、受付中の次NMI、EI終了境界のNMI、IM2の表境界とSPL24の全幅折返しを検証する。
- プレフィクス付きRETI／RETNとADL ED75hがSPS／SPLを変更する前に停止すること、診断なしビルドでは必要なP2をNOT READYにすることを検証する。

単体の全16MiB RAMを使うSPL全幅折返しはCPU機能検証であり、未マップ領域のある実機SDRAMで同じスタックを使えるという意味ではない。
完全なMSX-DOS／BIOS、全NMI／IRQ／WAIT組合せ、DMA／BUSRQ、電気的なCDC、GOWIN実タイミングの証明ではない。
公式仕様参照：Zilog eZ80 CPU User Manual UM007715-0415 https://www.zilog.com/docs/UM0077.pdf
