# R37用の拡張FUSE

CPUソースは親プロジェクトのfpga/G80A_eZ80を直接ビルドする。R36から変更したLD A,I/Rの64条件は全PASS。全体では27,170件実行、25,232件完全一致、1,938件未一致で、全PASSではない。

元の28,290件と期待値はsuiteに変更せず保持。992件の方針除外、128件の未実装は未実行。baseline_r36には以前の比較結果を保存している。

```sh
python3 tools/build_dut.py
python3 tools/audit_suite.py
python3 tools/run_fuse.py --match '^ED_(57|5F)_' --name ldair_r37
python3 tools/run_fuse.py --name full_r37
python3 tools/run_fuse.py --events-only --name events_r37
python3 tools/analyze_r37.py
python3 tools/verify_comparator_r37.py
```

全体run_fuseは既存の未一致が残るため終了コード1が正常に予想される。対象64件の実行は終了コード0を期待する。対象外の比較結果がR36から変わっていないことはanalyze_r37.pyで確認する。

```sh
python3 tools/show_case.py ED_57_a0_native_s0
python3 tools/show_case.py ED_A2_a1_native_s0
```

後者のINIは未修正であり、不一致が表示される。I/Rフラグの独立式10,240件と実COM回帰は親プロジェクトのtools/verify_r37.pyから実行する。

確認環境：Python3、GHDL5.0.1、Icarus Verilog11.0。GHDL/IVERILOG/VVP/IVL_ROOTで場所を指定可能。元ZIPの復旧経緯・制限とR36の過去の結果はdoc/baseline_r36/RESULTS_JA.mdを参照。現在の集計はdoc/R37_FUSE_SUMMARY.json。
