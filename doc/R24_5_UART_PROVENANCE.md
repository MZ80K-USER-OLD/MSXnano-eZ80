# UARTデバッグ回路の継承関係

2026-11-22確認。

* 元プロジェクト：jabadiagm/MSXgoauldSD_tn20k（main）
* MSXnano：RetroSilicon/MSXnano（standalone）。GitHub上も前者を親とするfork。
* 現在のeZ80基準版：RetroSiliconの拡張loggerを維持している。

Goa'uldにも `fpga/src/msx2p_debug.v` と `fpga/msx_debug/` があり、UART監視機能の基本部分は継承されている。
RetroSiliconではfpga/msx_debugに元の実装を残し、実際に使用するfpga/src/msx2p_debug.vを拡張している。

LFへ正規化したGit blob SHA-1で確認した対応：

| 現在の基準版のファイル | blob SHA-1 | 確認できた対応 |
|---|---|---|
| fpga/src/msx2p_debug.v | 71b9772ee9d3b03b551fd1646f1cab90c008bc13 | RetroSilicon standaloneの同名ファイルと一致 |
| fpga/msx_debug/msx2p_debug.v | 9a33fbe1194d855003cd1b090e229296983b215d | Goa'uld mainとRetroSiliconに残る旧実装が一致 |
| fpga/src/print.v | ccb35beb2031ffb083db6db329a90b93232cceae | Goa'uld / RetroSilicon双方と一致 |
| fpga/src/uart_tx.v | 13fa7940af7deb1b3e61792e2fe61594831b1cc4 | Goa'uld / RetroSilicon双方と一致 |

元のmsx2p_debugは11,385 bytes、現行の拡張版は33,241 bytes（いずれもLF換算）。
現行にはスロット・マッパー・音源・VDPなどの監視値とカウンタ、文字列出力の拡張が含まれる。
eZ80化のために今回追加した回路ではない。

本検討で示した2,291 LUT / 290 ALU / 678 Register / BSRAM 1は、現行基準版のdebug階層の合成結果。
Goa'uldの元の小さいloggerのリソース使用量ではない。
元プロジェクトの各ビルドで有効かどうか、導入コミットや個々の拡張の作者までは今回の確認対象に含めない。

一次ソース：

* https://github.com/jabadiagm/MSXgoauldSD_tn20k
* https://github.com/jabadiagm/MSXgoauldSD_tn20k/blob/main/fpga/src/msx2p_debug.v
* https://github.com/RetroSilicon/MSXnano
* https://github.com/RetroSilicon/MSXnano/blob/standalone/fpga/src/msx2p_debug.v

診断版では、この現行拡張loggerを変更せず使用する。
通常版ではGPRJが同じインターフェースの無効実装を選択する。
