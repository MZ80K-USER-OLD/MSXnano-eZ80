# R22から残る工程

対象内の未実装8ニーモニックはR22でRTL追加した。専用COMはEZ80IOR /RUN。GOWIN・実機確認はこれから。

1. R22の合成・Logic/LUT・Setup/Holdレポート、EZ80IOR/EZ80MEM/EZ80IO2/RUNALLおよびSOFARUNでの実機回帰。
2. JP/CALL/RET/RST/RETI/RETNの幅suffix・混在モードを公式の有効形式と照合し、未対応の有効形式を解消する。
3. 全対象命令の形式・境界・フラグについて独立検証を拡充。現在の有限テストPASSを全ISAの証明にしない。
4. Setup/Holdを実際の捕捉・保持条件と照合し、タイミングを改善する。制約の一律緩和はしない。以前の実機メモリ不具合の厳密な原因も未確定。

SLPはNOP、TRAPと16bitポート上位8bit固定0の追加命令群は対象外の方針を維持。
詳細は[命令一覧](EZ80_INSTRUCTION_STATUS_R22.md)、[R22追加内容](R22_BLOCK_IO_REPEAT.md)。
