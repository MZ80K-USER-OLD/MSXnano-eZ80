# MSXnano T80 eZ80 再構築 R11

**大工程7：通常ADL（MADL=0）のIM1／IM2／NMI、RETI／RETN。**
R10のGOWIN合成・LUT85%・CTL／ADL／F9の実機PASS・SofaRunからスペースマンボウのプレイを基準とする。
R11のGOWIN合成・配置配線・タイミング・LUT使用率・実機動作は確認待ち。

ZIPを短いパスの新しいフォルダへ完全展開し、次のGPRJで全ビルドしてR11を書き込む。

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

R10で成功したDual Purpose Pin設定を維持し、SystemVerilog 2017を確認する。GPRJ／CST／SDCはR10から変更しない。

## 実機テスト

先行配布P2のCOMをそのまま使う。更新不要。

```
EZ80IRQ /RUN
EZ80IM2 /RUN
EZ80NMI /RUN
```

期待表示は各 `P2: PASS`。同梱GPRJは診断接続を有効にしており、R11でのNOT READYは合格ではない。
追加の確認は `EZ80I16 /RUN` と `EZ80RST /RUN`（期待：P2: PASS）。
R10までの `EZ80CTL /RUN`、`EZ80ADL /RUN`、`EZ80F9 /RUN` も回帰し、SofaRunからスペースマンボウのプレイを確認する。
実機用COM20本と一括実行用BATをZIP直下と `hardware_test` に含む。`sim` のCOMはシミュレーション専用。

P2のMIX／MB／MAD／TST／LDH／LDXは未対応のためNOT READYが正常。引数なしのREADYも機能試験の合格ではない。

## 今回の範囲

割り込みの復帰PCを24bit SPLへ3バイト保存し、WAIT完了後・命令／ブロックのバイト境界で受付する。
NMI優先、受付中の次NMI、EI直後のNMI、RETN後の許可復元を検証する。IM2に必要な16bit I転送も先行実装する。

P2の診断入力・ベクタ接続はCPUラッパー内に実装し、D8を受けるまで無効。テスト中だけ通常INTをマスクし、ベクタ読出しをプライベートSDRAMへ切り替える。BIOS ROMは書き換えない。
IRQ／NMIはINT_n／NMI_n入力経路を通す。基板の外部NMIピンを実機検証したものではない。
MSX-DOS／BIOSがEIする可能性を考慮し、ADL・ベクタ切替中は呼ばず、Z80／通常接続へ戻してから出力する。メモリ不一致はADDR／EXP／ACTを表示する。

リセットはZ80互換・拡張ロック。元G80A、メモリブリッジ、SDRAM制御、VDP優先仲裁、タイミング制約を維持する。一律の制約緩和は追加しない。
ADL IM0は受付を抑止し、未対応。MADL付き割り込み・混在復帰フレーム・MBASEは工程8以降に残る。上位00h固定の追加I/O命令は除外方針を維持する。

詳細：`doc/RESTART_R11.md`。進捗：`doc/ROADMAP.md`。T80拡張時の注意：`doc/T80_EXTENSION_NOTES.md`。
機能検証結果：`verification_result.json`。再現：`bash tools/run_checks.sh`（GHDL／Icarusが必要）。
