# EX3872修正

top.v/top_ez80.vの外部バスポート宣言がコメントアウトされている一方、代入先に未宣言の名前が残っていた。
ex_bus_m1_n/rfsh_n/mreq_n/iorq_n/rd_n/wr_n/data_reverse_nと8bit ex_bus_mpを内部wireとして明示宣言。
使用されるバス別名も含むため代入を削除しない。FPGA外部ポートやCSTピンは追加しない。
全ex_bus_*名の明示宣言を両topで静的確認。
元のT80と上位8bit機能、階層タイミング修正を保持。Gowin合成は未実行。
この成果物はT80/eZ80プロジェクト用。別のfz80_MSXソースを検査したものではない。
