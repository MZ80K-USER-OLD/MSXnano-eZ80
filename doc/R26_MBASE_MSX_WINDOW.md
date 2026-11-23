# R26 実装・検証範囲

## 基準と変更

基準はユーザーがEZ80MEM／EZ80TIO／RUNALLとSOFARUNからスペースマンボウを実機確認したR25。R24.6のFF比較版は採用しない。

| RTLファイル | 変更 |
|---|---|
| fpga/G80A_eZ80/t80_pack_ez80.vhd | CPUコンポーネントにA_MSX_MATCH出力を追加 |
| fpga/G80A_eZ80/t80_ez80.vhd | Address_Bank_RegとMBASEの8bit一致を出力。Z80拡張ロック時に、次アドレスbankも00hへ整合 |
| fpga/G80A_eZ80/g80a_ez80.vhd | 一致信号を要求T1で捕捉。診断ベクタの対象をnative bank00／移動したMSX窓へ拡張。E4h=26h、E5h=D9hの診断読出し能力ID |
| fpga/src/ez80_memory_bridge.v | private RAMの下限01hを除き、00h～1Bhに変更 |

レジスタファイル、ALU、命令デコーダ、実行制御幅、SD-RAMコントローラ、top、VDP、SDC／CST／GPRJはR25と同じ。SLP／TRAPやI/O命令の対象方針も変更しない。

## 信号と捕捉

`A_MSX_MATCH = (Address_Bank_Reg = MBASE)`。MBASEを付加して作ったアドレスかという由来ではなく、最終アドレスの一致結果である。ADLで明示した24bitアドレスも一致ならMSXへ入る。

命令単位に固定せず、ブロック転送の読出し・書込みやバンク境界をまたぐ各メモリ要求で判定する。データ幅やSPS／SPLの選択を、この信号で変更することはない。

ラッパーはCLK下降・clk_falling有効・TState=001の同じエッジでRequest_Address、Request_MSX_Address、Request_Extendedを捕捉する。非一致ならMSXアドレスを0000hへ遮断する。WAIT／CEN停止中に現在のMBASEで再分類しない。書込みデータは従来どおりT1／T2で保持し、有効期間は変更しない。

I/O／IACKの既存処理は捕捉時に優先。refreshは一時的に既存MSX refresh経路を出し、終了後は保持済み要求へ戻る。BUSAK時のハイインピーダンス処理も既存のまま。今回の新規試験はBUSRQの全位相を網羅するものではない。

比較は組合せ出力、保持は既存ラッパーFFを利用する。CPUに1サイクル遅延するタグFFを追加していない。比較器をCPUへ置くことだけでLUTや物理段数が減るとは扱わない。

## 診断ベクタ

DIAGNOSTICSとDiag_Activeが有効なメモリ読出しで、下位0000h～007Fhかつ、bank00hまたはMSX一致なら、読出しをprivate bank0Fhへ振り替える。書込み・I/O・IACK・refreshには適用しない。

このoverrideが最終の行き先で、MBASE=0Fhでもprivate 0FhをMSXへ再分類しない。MSX側アドレスは0000h、MREQ無効にする。

通常動作で診断が無効なら、MBASE非ゼロ時のADL IM1=000038h、NMI=000066hは物理640038h／640066hへ接続される。必要なハンドラをソフトウェアが準備する。MSX BIOSをADLハンドラとして自動利用する変更ではない。

## 実機用COM

新規EZ80WIN.COMと更新EZ80MB.COMは、MBASE=00h／0Eh／0Fh／FFhを試験する。ADL明示24bitのMSX一致、短いデータのMBASE使用、非一致bank01、07FFFFh／080000h、非ゼロMBASE時のprivate bank00、MSX側Z80フェッチ、SPS／SPL保持を比較する。FFhケースはprivate bank00のRST 38hベクタも準備し、ADL RSTからの復帰を確認する。MSXのベクタ／FFFFhへは書き込まない。

不一致はStage／ADDR／EXP／ACTを表示する。結果をprivate RAM経由で回収する項目も、表示するADDRは検査対象の論理アドレスとする。ただしスタック等のスナップショット比較はスナップショットのアドレスとなる。

テスト中の拡張処理はDI。DOS呼出し前にMBASE=0・Z80モード・拡張ロックへ戻す。DOS／BIOSがEIすることを前提に、以後の拡張処理前は再度DIする。シミュレーションのBDOSスタブも内部でEIし、IM1を実際に受け付ける。

TIO／NP6／ION／DECの共通テンプレートは、Z80側コードをMSX 8200hへ置き、MBASE=0で実行する配置へ変更した。既存COMとの混在を避けるため同梱版を更新する。

旧R25のMBを含む全旧COMをlegacy_R25へ比較用に保存。既存RUNALLで使わない追加診断のうち、非ゼロMBASE上のprivate Z80コードを前提とするRS8／IM0／PFX／RW2／MX1等は有効配布から退避した。これらの移行、全命令別の再回帰は残課題。

## ローカル検証と限界

- GHDLで実RTLを解析・Verilogへ変換し、IcarusでCPU／ブリッジ／SD-RAM RTLと機能モデルを実行する。
- 要求保持の単体試験：全256MBASE×全256bank、読書き／I/O／IACK／refresh／診断、WAITとCEN停止。故障注入で隔離・要求破損の検出も確認する。
- WINの実COMは通常／位相変更／CEN停止／低速CPU、故障表示、/RUNなし、拡張なし、旧機能応答を検証する。bank00の物理要求アドレスも照合する。
- ADL IM1／NMIは別のMSX／拡張RAM配列を使った機能試験で、WAIT／CEN停止あり・なしを検証する。このIRQ試験自体は物理SD-RAMモデルを使わず、SD-RAM接続はWINの実COMとRST試験で別に確認する。
- 既存CPU回帰、メモリ故障検出、MR4、RUNALLで使う実COMを確認する。正確な実行数はR26_VALIDATION.jsonを参照。

RTL機能シミュレーションであり、GOWINネットリスト、実機のSD-RAM電気的条件、全MSX BIOS／DOSの証明ではない。新しい8bit比較からRequest_Extendedへ入るSetup／Holdと、既存の命令デコード→Request_Extended経路をGOWINで確認する。制約の一律緩和は行わない。

## 残す項目

I/O経由のMBASE書込み、ADL読出し、TARGET_PC付きADL切替は未実装。既存の診断C8hによるMBASE読出しは維持する。GSR利用は保留。大きな旧診断COMの移行と、R26実機・GOWINタイミング／使用量の確認を次段階で行う。
