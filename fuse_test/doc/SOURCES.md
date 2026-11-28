# 仕様と参照元

- Zilog eZ80 CPU User Manual UM007715-0415: https://www.zilog.com/docs/UM0077.pdf
- 公式説明の検索索引で確認した箇所：Registers and Bit Flags / CPU registers in Z80 mode、Memory Mode Switching / suffix examples、LD A,I、LD A,MB、INI、Interrupt Mode 0、混在割り込み表21–24。
- 提供ZIPの生成元・固定コミットは suite/PROVENANCE.md を参照。CEmu d7679d04c44741359b1f3a0444ff4eea99c34369、zdis 7eb89e56d219bbca5ca5cd82c98dce69bd75004b。
- 公式PDF URLは現在のアクセス経路では別ページへ転送され、PDFを今回新規ダウンロードできていない。仕様確認は公式URLの検索索引に取得できた該当節を用いた。原文全体をこのキットへ同梱・転載していない。
- 回収した参照ソースとライセンスはsuite/vendorに保持。CPUソースの権利表示はrtl各ファイル冒頭に保持。
