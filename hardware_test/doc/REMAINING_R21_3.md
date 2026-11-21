# R21.3から残る工程

## 実装する対象として明確に残る8命令

| 群 | 命令 | opcode | 作業 |
| --- | --- | --- | --- |
| I/Oアドレスも更新して反復 | INI2R | ED94 | DEポート、BC回数、HL/DE前進 |
| 同上 | IND2R | ED9C | HL/DE後退 |
| 同上 | OTI2R | EDB4 | 出力、HL/DE前進 |
| 同上 | OTD2R | EDBC | 出力、HL/DE後退 |
| I/Oアドレス固定で反復 | INIRX | EDC2 | DEポート固定、BC回数、HL前進 |
| 同上 | INDRX | EDCA | HL後退 |
| 同上 | OTIRX | EDC3 | 出力、HL前進 |
| 同上 | OTDRX | EDCB | 出力、HL後退 |

既存のIO2転送行・byte ALU・レジスタ/要求保持を共用する方針。反復境界IRQ/NMI、WAIT、幅、ゼロからの回数、境界、フラグを別途検証する。

## 8命令以外の残り

1. JP/CALL/RET/RST/RETI/RETN等のsuffixごとの対応範囲を公式仕様と照合。有効な未対応形式を解消する。
2. 対応する全命令・形式・フラグの独立検証。既存RUNALL全PASSを全ISAの証明としない。
3. GOWIN Setup/Holdの捕捉条件・保持期間を照合。証明のない一律multicycle/false_pathを入れない。
4. 規模の確認、最終実機回帰。以前のメモリ不具合の原因特定は継続課題。

したがって「残りは8命令だけ」とは数えない。命令追加、形式監査、網羅検証、物理タイミングの作業は別に残る。

## 完成条件から除外

- SLP: 非対応、拡張有効時NOP。省電力・起床は実装しない。
- 未定義命令TRAP: 非対応。97ニーモニックには含めない。
- IN0/OUT0/TSTIO、INIM/INDM/OTIM/OTDMとそれぞれの反復形: 16bit I/Oポートの上位8bitを00H固定する追加命令として対象外。

詳細な命令ごとの状態と現在のopcode解釈はEZ80_INSTRUCTION_STATUS_R21_3.md。
