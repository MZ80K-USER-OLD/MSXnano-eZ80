# R25：TSTIO実装

R24.5の実機確認済みRAM併用版を基準に、`ED 74 nn` のTSTIOを追加しました。R24.6のFF比較版は採用していません。

開くプロジェクト：`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`（通常版、UARTログなし）。診断UART付きは従来どおり `fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj`。

**GOWIN合成・配置配線・LUT使用量・実機動作は未確認です。** ローカル検証結果は `doc/R25_VALIDATION.json` を参照してください。タイミング収束を主張しません。

ZIPを新しいフォルダへ展開してからGOWINで開いてください。ビルド設定はR24.5と同じで、`fpga/configure_normal.tcl`／`fpga/build_normal.tcl` を使用できます。

## 実機確認

1. R25を合成・配置配線して、新しく生成したbitstreamを書き込む。
2. `EZ80MEM /RUN` を最初に単独実行し、PASSを確認する。
3. **今回同梱の新しい `EZ80TIO.COM`** をコピーして `EZ80TIO /RUN` を実行する。
4. `EZ80TIO R25: PASS` を確認する。
5. `EZ80MR4 /RUN`、`EZ80DEC /RUN`、`RUNALL.BAT`、SOFARUNからスペースマンボウの起動・PLAYを確認する。

MEMでFAIL/FATALなら次の試験へ進まず、Stage／ADDR／EXP／ACTを記録してください。

新COMは 16686 bytes、CRC32 **30505EB2**。以前のR22系と同名のEZ80TIO.COMを使わず、今回のR25版へ更新してください。既存34本のCOMは変更せず、RUNALLにTIOを追加しました。新COMはrootとhardware_testの両方に含みます。

`CASE 0`～`CASE 9`を表示してからPASSします。`/RUN`なしはREADY、旧CPUや診断なしはNOT READY／UNSUPPORTEDで終了します。不一致時はStage／ADDR／EXP／ACTを表示します。

仕様・保持タイミング：`doc/R25_TSTIO.md`。残項目：`doc/ISA_STATUS_R25.md`。
