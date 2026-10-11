# MSXnano T80/eZ80 v9

実行時の短長モード遷移と02h/03hフレーム復帰の基盤を追加。
全命令ADL対応ではない。対応範囲はDOCM/ADL_PROGRESS_v9.mdを参照。

GHDL: bash run_baseline.sh（GHDLとPython3）。251実行PASS。
新規: sim/tb_mixed24.vhd（テストプログラムも内包）。ログ: test_results_v9.log。
MSX実機用設定は従来と同じ。新機能用のメモリ接続・実機COMは未実装。
v9のGowin合成・実機動作は未確認。
eZ80プロジェクト: fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj。
元T80プロジェクト: fpga/project_T80/MSXNanoTang20K_T80.gprj。
既存EZ80V4.COM/EZ80DIAG.COMとそのASMは旧拡張機能の実機回帰用として同梱。
