# R30：実行側の命令・プレフィクス再判定を削減

実機確認済みR29.2を基準に、ペア転送・24bit演算・LEA/PEA・JP間接・SP即値ロードの静的選択を、命令確定時に保持する制御へ移しました。
FPGAの変更はCPUとパッケージの2ファイルだけです。追加サイクルはなく、命令パイプライン化は行いません。

GOWINでは `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` を別フォルダから再ビルドしてください。R30のLogic使用量・Setup/Hold・実機動作は未確認です。LUT削減・タイミング改善はまだ確定していません。

COM30本とRUNALL.BATはR29.2と同一で、FLASH上のテストを更新する必要はありません。

まず `EZ80MEM /RUN`、`EZ80MR4 /RUN`、`EZ80ALU /RUN`、`EZ80LEA /RUN`、`EZ80LDH /RUN`、`EZ80LDX /RUN`、診断MX0/MX1/MX2/MA1を実行し、RUNALL全項目、SOFARUNからスペースマンボウの起動・PLAYを確認してください。

- 変更内容・保持タイミング・残る再判定：doc/R30_EXECUTION_DESCRIPTOR.md
- ローカル検証結果：doc/R30_VALIDATION.json
- R29.2とのRTL差分：R29_2_to_R30.patch
- 再検証：tools/verify_r30.py（GHDL、Icarus、Python3を使用）

再検証スクリプトではツールの場所を環境変数 `GHDL`、`IVERILOG`、`IVL_ROOT`、`VVP` に指定します。`IVL_ROOT` はIcarusのivlライブラリディレクトリです。

R29.2は機能確認済み基準として保持してください。過去版名のtools/docは履歴資料であり、現在版の監査にはverify_r30.pyを使います。
