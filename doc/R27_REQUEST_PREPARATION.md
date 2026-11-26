# R27：要求保持前の選択回路の分割

## 実装範囲

変更RTLはfpga/G80A_eZ80/g80a_ez80.vhdの1本。CPU本体、命令デコーダ、レジスタファイル、ALU、ez80_memory_bridge、memory_ez80、top、VDP、GPRJ／SDC／CSTはR26と同一。

比較を明確にするため、今回は要求保持前の段だけを変更する。接続先を物理アドレスへ変換した後の新しいキュー、CPUメモリ要求の共通仲裁、VDP／SDRAMの捕捉位置変更は含めない。

## 従来と新しい保持位置

| 段階 | R26 | R27 |
|---|---|---|
| CPU出力 | アドレスbank、MBASE一致、Write、IORQ等 | 同じ |
| 54MHz立上り準備 | なし | Prepared_Bank[7:0]、Prepared_Extended、Prepared_IO、Prepared_Writeを毎立上りで保持 |
| CPU有効T1・54MHz立下り | 読書き／IACK／診断ベクタ等を組合せで選択しRequest_*へ保持 | Prepared_*からRequest_*へ保持。下位アドレスはCPUの保持済みA_iを使用 |
| 書込みデータ | T1／T2でRequest_Dataへ保持 | 変更なし |
| 要求中 | WAIT／CEN停止中も保持 | 変更なし |

追加する準備レジスタの記述幅は11bit。低位16bitのRequest_AddressとRequest_MSX_Addressは同じ入力・捕捉条件となるため、合成時に保持FFを共有できる余地もある。合成後の純増FF／LUTは配置配線で評価する。MSX下位アドレスはRequest_MSX_Addressへ常に取り込み、拡張時の0000h遮断は既存A_MSX出力側の1箇所に集約する。外部へ出るMSXアドレスとMREQの隔離は維持し、内部ペイロードを隔離判定に再使用しない。

## 準備する判定

1. 通常はCPU bankとMBASE一致結果でMSX／拡張を決める。
2. 診断ベクタ読出しならbank0Fhと拡張側を選択する。
3. I/OまたはIACKのMC1はbank00h・既存MSX/I/O側を優先する。
4. IORQとWriteも同じ準備段で保持する。

診断ベクタのWrite判定に残っていた命令デコード由来の組合せ経路は、準備FFを挟む。後段の要求FFのDへIR由来の選択を直接つなげない。I/O／IACK／refreshのバスストローブ生成や、SD-RAM仲裁への経路全体を変更したわけではない。

## 時間条件

準備段はCPU CEで間引かず、54MHzの毎立上りで更新する。CPUがT1へ入った後、要求を捕捉する有効立下りまでに、安定した同一サイクルの出力を採る立上りが必要。

本MSXnanoの約3.6MHz用CE／falling配置を対象にする。CPU_DIV=4／16の実CPU試験、位相変更・CEN停止・WAITを確認する。CENを常時1にするフル54MHz CPUや、T1へ入る立上りの直後の立下りで即要求捕捉する別インタフェースは、この版の対応を保証しない。CE/fallingの配置を変える場合は準備時間を再検証する。

この条件は機能上の捕捉整合性の条件であり、Setup／Hold例外の根拠として自動適用しない。Prepared_* FF自体は毎54MHzで更新されるので、そこへの経路は実クロック周期で満たす必要がある。

T1捕捉後にPrepared_*が次の値へ進んでも、外部バスはRequest_*を使用する。アドレス／読書き／MSX選択を一つ前の要求へ混在させない。WRITEデータはT2まで更新可能なので、準備段ではデータを固定しない。

## 期待する効果と測定範囲

IR→デコード→診断等の選択→立下りRequest FFという半周期経路を、IR等→立上りPrepared FFと、Prepared FF→立下りRequest FFに分ける。命令IRからPrepared FFまでは54MHzの1周期経路となることを狙う。

ただし最適化後の論理複製、配線、ファンアウト等で結果は変わる。全体タイミング収束やLUT減少を保証しない。Request_Extended→MSXスロット／MegaRAM→SDRAM制御の経路、およびVRAM読出し→スプライト制御やHold違反は、直接の改善対象ではない。

外部メモリ要求への新しい受付キューや追加WAIT段は設けていない。準備段が有効T1に間に合う構成で、R26と同じバスサイクルを保つ。今後、要求保持後のパイプラインを追加するときは別途早期WAITと要求受付／完了の規則を設計する。

## 検証

- R26の正確なラッパーをsim/reference_r26へ保存し、変更していないCPU RTLと組み合わせて参照CPUを生成する。
- 同じDI／WAIT／割り込み／CEをDUTと参照CPUへ与え、毎54MHzの立上り・立下り後にA24、MSX16、拡張選択、MREQ／IORQ／RD／WR／RFSH／M1／HALT、DOを比較する。
- メモリ／制御／ブロック／LDX／TSTIO／割り込み／混在モードの実COMで比較する。位相・CEN停止を加えた比較も行う。
- 全256MBASE×全256bankの要求保持単体試験は、T1準備の立上りを経て捕捉する刺激へ更新する。故障注入も実行する。
- WIN／TIO／MEM／MR4／IM1／NMI／ロック、CPU回帰、RUNALLの実COMを実行する。

機能モデルであり、GOWINネットリスト遅延や実機のSD-RAM電気的動作の証明ではない。実行結果はR27_VALIDATION.jsonを参照。
