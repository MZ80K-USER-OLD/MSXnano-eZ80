# R23 実機用テスト

新規: EZ80IRX.COM /RUN（4つの固定ポート反復I/O）、EZ80TIO.COM /RUN（TSTIOと除外8命令のNOP）。
新しいRUNALL.BATもコピーしてください。旧EZ80IO2/EZ80IORは履歴として残りますが、R23ではNOT READYです。
詳細は ../doc/R23_IO_SCOPE.md を参照。

以下は従来テストの履歴です。

# R22追加テスト

`EZ80IOR /RUN` → `EZ80IOR R22: PASS`。32ケース、CRC32 `643ACD66`、53097bytes。R22 FPGAが必要。詳細は[実装・試験説明](../doc/R22_BLOCK_IO_REPEAT.md)。
