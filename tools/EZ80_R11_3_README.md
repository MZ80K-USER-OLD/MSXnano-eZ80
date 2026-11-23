# MSXnano T80 eZ80 再構築 R11.3

R11.2で残ったタイミング経路に対する、MSX要求の分離保持・命令分類・SDRAM捕捉エッジの修正版です。
**R11.3のGOWIN合成・配置配線・資源量・実機動作は未確認です。タイミング達成を保証する版ではありません。**

## ビルド

ZIPを新しい短いパスへ完全展開し、次のプロジェクトで全ビルドしてください。

`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

GPRJ／CST／SDCはR11.2と同一です。SystemVerilog 2017と同梱制約ファイルを使用してください。
新しいfalse path／multicycleや、max_delay／クロック遅延の緩和・相殺は行っていません。

## 変更点

- 全24bit要求と同時に、MSX用の遮断済み16bitアドレスと拡張要求フラグを保持します。周辺回路への経路から要求後のバンク比較・アドレス遮断MUXを外します。
- 非ゼロバンクのxxFFFFhは引き続きMSXスロットレジスタから隔離します。I/O、リフレッシュ、診断ベクタ、ADL割り込み入口の扱いも維持します。
- IRと同時に保持する命令分類を6bitから16bitへ増やし、演算・制御移行などの入口分類を前倒しします。新しい命令機能やフェッチパイプラインの追加ではありません。
- SDRAM側は、同期・アーム後の108MHz下降エッジでpayloadを捕捉し、次の上昇エッジで受理を公開します。VDP優先、CPUのWAIT、リフレッシュ、応答までの保持、既存スロット選択は維持します。

詳細、捕捉時点と保持契約、残るリスクは`doc/TIMING_R11_3.md`に記載しています。
反対エッジ化で生じる半周期経路も含め、実際のSetup／Holdの成否は次のGOWINレポートで確認します。

## 実機テスト：FLASH更新不要

先行配布したCOM20本はすべて同じバイト列です。追加・書換えは不要です。
`EZ80MEM /RUN`、`RUNALL.BAT`、SofaRunからスペースマンボウの起動・プレイを確認してください。

| テスト | 期待結果 |
|---|---|
| EZ80D3 | R3: PASS（引数なし） |
| EZ80MEM／ALU／BLK／MUL／LEA／ADL /RUN | P1: PASS |
| EZ80F9 /RUN | R9: PASS |
| EZ80CTL /RUN | R10: PASS |
| EZ80IRQ／IM2／NMI／I16／RST /RUN | P2: PASS |
| EZ80LDH／LDX／MAD／MB／MIX／TST /RUN | 未実装のためNOT READY |


BATには総合PASS判定がないため、各行を確認します。上記6本のNOT READYは未実装機能を示す正常な表示です。
メモリ不一致のADDR／EXP／ACT表示、ADL中にMSX-DOS／BIOSを呼ばず状態復帰後に表示する方針も維持しています。
COMはZIP直下、プロジェクト直下、hardware_testに同じものを収録しています。

## 検証・工程

基準R11.2はGOWIN合成成功、Logic 17,787（86%）、CLS 9,742（94%）、BSRAM 43/46。
実機でEZ80MEMとRUNALLの対応済みテスト全PASS、未実装6本NOT READY、SofaRunからスペースマンボウのプレイを確認済みです。
ただしR11.2の54MHz系Fmaxは29.777MHzで、Setup違反996端点、Hold違反75端点が残っています。

R11.3は235条件の正試験と8件の故障注入の期待失敗を確認します。最終結果は`verification_result.json`、ログは`verification_logs`。
追加の要求レジスタ試験は診断あり／なし各75,776チェック。CPU＋SDRAM回帰も新しいMSX分離接続で実行します。
再現入口は`bash tools/run_checks.sh`（GHDL／Icarusが必要）。全MSX BIOS／DOS起動や全FUSE、物理遅延の検証ではありません。

大工程7の実装済み範囲を維持し、工程10のタイミング対処を先行しています。
ADL IM0、MBASE、MADL、混在CALL／RET／割り込みフレーム、追加ロード、TST系は未実装です。
次のレポートではFmaxだけでなくSetup／Holdの詳細、捕捉FFのエッジ、Logic／CLS／BSRAM、PR1014を確認します。
