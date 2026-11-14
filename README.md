# MSX eZ80

eZ80 Implemented for MSX

R14（実機確認済み、Logic 92%）を基準に、拡張命令の **Write判定だけ** を疎なマトリックスへ置き換えた比較版です。新しい命令実装の版ではありません。展開直後はマトリックス版が選択されています。

## 変更範囲

変更したFPGAソースは `fpga/G80A_eZ80/t80_mcode_ez80.vhd` の最終Writeプロセスだけです。登録済みWrite_Class × MCycleに、データ幅・ストリーム幅・ADL・プレフィクス・割り込み条件を組み合わせます。15行の有効条件と8行の非ゼロ出力をOR合成し、該当しない場合は従来Z80のLegacy_Writeを通します。

従来の上書き優先順位を維持しています。特に、通常のゼロ出力ガードとネイティブADL割り込みが重なる条件では、後段にあった割り込み処理が優先されます。主デコードと他の48制御出力は変更していません。CPU全体のデコードをマトリックス化したものではなく、パイプライン段も追加していません。

FF、ワークレジスタ、FSM状態、制御ビットの追加はありません。CPU本体、ラッパ、16bit MSXバスと24bit拡張バスの分離、$FFFFセカンダリスロット遮断、SDRAM、VDP、PAL/YJK、GPRJ、CST、SDCはR14と同一です。IN0/OUT0など上位I/Oを00固定する追加命令も実装していません。一律の制約緩和や新しいマルチサイクル指定はありません。

## GOWINでの比較

使用プロジェクトは両版とも次です。

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

1. 今のR14の実装出力（implフォルダ）、レポート、動作確認済みビットストリームを別の場所に保存してください。
2. 展開先のプロジェクトルートで `USE_R14_DECODE.cmd` を実行し、GOWINで全体を再ビルドします。R14の比較用レポートを別名で保存します。
3. `USE_MATRIX_DECODE.cmd` を実行し、同じ設定で全体を再ビルドします。R14.1のレポートを別名で保存します。
4. 実LUT数とタイミングを比較します。

両cmdはWindows PowerShellを使用します（Python不要）。保存された2種類のソースと現在のソースのSHA256を確認します。ユーザー編集が入った場合は上書きせず停止します。実行後、GOWINでソース変更を反映して再ビルドしてください。cmdのWindows上での実行検証は未実施です。Python版の同等操作は検証済みです。

Pythonがあれば、同じ切り替えができます。

```text
python tools/select_decode_r14_1.py baseline
python tools/select_decode_r14_1.py matrix
```

| 比較項目 | 判定方法 |
| --- | --- |
| 実LUT数 | 詳細レポート中のLUT数を比較。増加ならR14へ戻す |
| Logic/ALU/CLS使用量 | LUT以外への増加や配置余裕も確認 |
| デコード段数 | 同じ始点・終点のLogic LevelとData Delayを比較 |
| Setup/Hold | WNS/TNS、違反数、54MHz/108MHzやクロック間経路を確認 |
| 合成・配置条件 | GOWIN版、デバイス、DualPin、言語設定、最適化、制約、配置シードを揃える |

R14の既知値は **丸められたLogic 92%** です。R14の実LUT数・今回の段数・今回のFmaxは未計測です。過去R13の詳細レポートをR14の実測値として使っていません。マトリックス化で論理上の直列上書きを避けても、GOWINの最適化・ファンアウト・配置配線によってLUTや遅延が増える場合があります。

詳細レポートをテキスト形式で保存したら、次の補助スクリプトも使えます。

```text
python tools/compare_decode_reports_r14_1.py R14_report.txt R14_1_report.txt --revert-if-lut-increases
```

実LUT数が増えた場合だけR14ソースへ戻します。Logicの割合だけでは自動判定しません。レポートの同一条件やタイミングの合否は人が確認してください。LUTが減ってもタイミング改善を保証するものではありません。

**戻した後はR14を再ビルドして書き込むか、保存したR14のビットストリームを書き込んでください。ソースを戻しただけでは実機は戻りません。** R14.1を検証するスクリプト群はマトリックス版を選択した状態で実行してください。

## 検証結果

- 全体回帰：550シナリオ合格、異常検出を確認する22シナリオも期待どおり。
- R14との全49デコード出力比較：8,388,608入力組み合わせ。除外なし。
- 最終Writeプロセスを双方の実ソースから抽出した比較：16,777,216件。全256種類のWrite_Class、全4種類のMode、ISet、全MCycle、幅、ADL、割り込み、Legacy_Writeの0/1を走査。
- 上位レジスタ、PC、SP、フラグ、バス動作の差分比較、WAIT、CEN停止、割り込み、バス要求、混在CALL/RETを回帰。
- R14への切り替えで全FPGAファイルがR14のSHA256へ戻ること、ユーザー編集時の停止を確認。
- LUT増加時の自動復元は合成レポートを模したテスト用データで確認。実際のGOWIN測定値ではありません。
- GOWIN合成、配置配線、実機確認はこのR14.1では未実施。全MSX-DOS/BIOSを含むボード全体のシミュレーションでもありません。

再実行の入口：`python tools/verify_r14_1.py`。GHDL、Icarus Verilogとpatchを使用します。`GHDL` / `IVERILOG` / `IVL_ROOT` / `VVP` で実行環境を指定できます。

## 実機用COM

**20本すべてR14と同一バイト列です。FLASHへのCOM書き直しは不要です。** ZIP直下、プロジェクト直下、hardware_testに同一COMを収録しています。

```text
EZ80MEM /RUN
EZ80MIX /RUN
EZ80MAD /RUN
RUNALL.BAT
```

期待値はMEM P1:PASS、MIX/MAD P2:PASSです。RUNALLでは `EZ80LDH`、`EZ80LDX`、`EZ80TST` の3本がP2:NOT READY、その他はPASSです。その後SOFARUNからスペースマンボウを起動してPLAYを確認してください。

DOS/BIOSの呼び出しが割り込みを再許可する条件を考慮した既存のテストを維持しています。メモリ失敗時のアドレス・期待値・実値の表示も変更していません。ADLリセット値は0、機能マスクは診断あり839F／診断なし039Fのままです。

R14でのユーザー確認：GOWIN合成成功、Logic 92%、MEM/MIX/MAD PASS、RUNALLの上記3本以外PASS、SOFARUNのスペースマンボウ起動・PLAY成功。

## 同梱資料

- `doc/R14_1_MATRIX.patch`：R14からの差分
- `doc/R14_1_DECODE_VARIANTS.json`：両版のSHA256
- `doc/r14_decode_baseline/`：保存したR14 CPUソース
- `doc/r14_1_decode_variants/`：マトリックス版の保存ソース
- `verification_result.json`：R14.1全体結果
- `verification_groups/`、`verification_logs/`：個別結果と実行ログ（R14という名前の検証スクリプトを再利用するものもあります）

R14以前のdoc・ツールは経緯確認用に残しています。今回の入口と結果はファイル名にR14_1を含むものと、このREADMEです。
