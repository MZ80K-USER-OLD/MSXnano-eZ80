# R28 実装範囲と時間条件

## 変更するRTL

| ファイル | 内容 |
|---|---|
| fpga/G80A_eZ80/g80a_ez80.vhd | Prepared_RD、Prepared_MREQ、Prepared_IORQ_n、Prepared_WR_nの4bitを追加。各ストローブの次値選択を立上り側へ移す |
| fpga/top_ez80.v | cpu_io_addr=cpu_addr24[15:0]を追加し、VDPのcsw／csr判定とmodeに使用 |

CPU本体、命令デコーダ、レジスタファイル、ALU、ez80_memory_bridge、memory_ez80、VDP本体、GPRJ／SDC／CSTはR27と同じ。GSRは保留。I/O経由のMBASE／ADL制御は追加しない。

## バスストローブの準備段

R27はアドレス・MSX選択等の準備段だけを追加し、RD／MREQ等の生成には命令デコード由来の組合せ経路が残っていた。R28では元の条件と代入順序を維持し、次の出力値を毎54MHz立上りで保持する。

- Prepared_RD／Prepared_MREQ／Prepared_IORQ_n／Prepared_WR_nは、最初に現在の出力値を採る。元の条件が成立しない場合の保持動作を維持する。
- 元のMCycle／TState／NoRead／Write／IORQ／IntCycle_nによる選択を、この準備FFのD入力側で行う。
- 有効立下りでは準備済みの値を出力FFへ移す。深いデコードを出力FFのD／CEへ直接渡さない。
- I/Oの初回T1では現在のIORQ_n_iを参照する。準備した次のIORQ値を使ってRDやWRを先に有効化しない。これにより元のI/O待機・ハンドシェイク順序を保つ。
- NoReadで要求を出さないサイクル、M1／IACK／refresh、T3での終了、出力保持条件を変更しない。
- WRに使うRequest_Write、Request_DataのT1／T2捕捉はR27と同じ。

Prepared_RD等はReset_sで初期化し、最終出力FFのリセットも元のReset_sのまま。R27から追加した記述幅は4bitで、合成後の純増FF／LUTは未測定。

## CE配置の条件

R27と同様、CPUが状態を更新した後、有効立下りの前に安定した状態を捕捉する54MHz立上りが必要。MSXnanoの約3.6MHz CE／falling配置を対象とし、CPU_DIV=4／16、位相変更、CEN停止、WAITで検証する。

CENを常時1にするフル54MHz CPU等へ、そのまま適用できると扱わない。PIPELINE_REQUEST=falseなら要求準備とストローブ準備を使わないR26相当のラッパー経路へ戻せるが、通常の配布はtrue。

出力を1 CPUサイクル遅らせたり、追加WAITを入れる方式ではない。既存の状態間にある54MHz周期を使って準備する。正しいCE配置でR26と同じ外部バス波形を保つことを比較する。CPUの命令フェッチ・実行全体のパイプライン化ではない。

## VDP専用I/Oアドレス

従来のVDPはbus_addrを使って98h～9Bhを判定していた。bus_addrは拡張メモリ要求時に0000hへ遮断されるため、Request_ExtendedがVDPのI/O制御まで伝わる組合せ経路が存在した。

R28ではVDPだけ、CPUのA24下位16bitをI/Oアドレスに使う。通常I/Oではラッパーが要求をI/O側へ分類し、A24下位16bitとMSX側下位16bitが一致するため、従来と同じポートへアクセスする。

VDPの有効条件は従来どおりIORQ=0、M1=1、RDまたはWR有効。メモリアクセス中はIORQが無効なので、下位0098h等でもVDPを選択しない。IACKはM1で除外する。refresh中もI/O条件は成立しない。

A24はrefresh時に一時的にrefreshアドレスを出すが、その期間はVDP I/Oを選択しない。VDPのmodeは非選択中に値が異なってよく、実際のCpuReqが有効な時のアドレス・データが一致することを検証する。

これはVDPポートに限った分離で、全周辺機器のI/Oバスを変更していない。MSXメモリ側bus_addr、MREQ遮断、セカンダリスロットFFFFhの判定は変更しない。24bit側のxxFFFFhがMSXへ漏れない構造を維持する。

VDP本体のクロック・リセット・VRAM接続・I/O latchは変更していない。アドレス経路からRequest_Extended依存を外す目的であり、VDP／SD-RAM間のHoldやVRAM読出し→スプライト経路の改善ではない。

## 検証範囲

1. ストローブ単体：元のR26ラッパーと、MCycle／TState／NoRead／Write／IORQ／IntCycle_nの1024条件、繰返しT1、立下り有効停止、リセットを比較。5121チェック。CPU内部状態を強制する条件試験で、実命令実行の代わりではない。
2. VDP I/O：現行topの実デコード式と、VDPの実I/O latchプロセスを取り出し、全65536下位アドレス×読出しI/O／書込みI/O／拡張メモリ読出し／IACK／MSXメモリ読出し／拡張メモリ書込み／MSXメモリ書込み／refreshを比較。CpuReq／CpuWrtと、CpuReq有効時のアドレス・データを照合する。VDP全体の描画シミュレーションではない。
3. 実CPU：同じ入力をR28と正確なR26参照CPUへ与え、毎54MHzの立上り・立下りで外部バスを比較。R27は既にR26と同じ波形であることを確認している。
4. 実COM：WIN／TIO／MEM／MR4、IM1／NMI／ロック、CPU回帰、RUNALLを使用。DOS内部でEIするスタブを維持する。COMバイナリは変更しない。

GHDL／Icarusの共有ベンチの版名として検証スクリプトやPASS行にR26／R27が残るものも、今回生成したR28 CPUモデルを使って新規実行する。

機能モデルであり、GOWINネットリストの物理遅延、実機、全MSX／VDP描画動作を証明するものではない。新しいFFへのSetup／Holdと、残った全体経路はGOWINで評価する。マルチサイクル／false-pathの一律追加は行わない。
