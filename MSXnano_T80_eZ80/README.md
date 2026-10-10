# MSXnano T80/eZ80 v5

PCと命令取得アドレスの24bit化基盤。ADL_PROGRESS_v5.mdを参照。
実機確認済みv4は前のZIPに保持。このv5はGowin合成・実機動作未確認。

拡張CPU: fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj
元T80: fpga/project_T80/MSXNanoTang20K_T80.gprj

MSX用設定ではFETCH24=falseで16bit動作。24bitアドレスはまだMSXメモリに接続していない。
実機でFETCH24を有効にしない。ADLモード未実装。
既存EZ80V4.COM/EZ80DIAG.COMは変更なし。新しいPC24機能は単体シミュレーションで検証。
GHDLとPython3でbash run_baseline.sh: 通常/WAITを含む27テストPASS。
