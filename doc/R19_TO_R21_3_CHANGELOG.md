# R19からR21.3までの追加・修正履歴

R19で追加したものも含む。厳密にR19を基準としてそれ以後の差分だけを見る場合は、R19の行を基準として読む。
R21.3の最終的な機能と、途中の試行を区別する。

| 版 | 種別 | 追加・変更内容 | R21.3に残るか | 主な確認 |
| --- | --- | --- | --- | --- |
| R19 | CPU機能追加 | ADLまたはMADL時のIM0。IACKの8種RSTとCD CALLを処理し、その他247値はNOP扱い。SPL/タグ付きフレームと既存CALL/RSTフレームを共用 | 残る | EZ80IM0、実機PASS |
| R19.1 | CPU修正 | 幅prefix＋DD/FD CB d opで、CB受理時に幅を確定。M6のインデックスアドレス計算前に幅を反映し、WAIT中は未消費、割込み境界を維持 | 残る | EZ80PFX、実機PASS |
| R20.1〜R20.5 | 試行・調査 | SLP停止/復帰/refreshと関連診断、メモリ調査案。実機停止等があり、R20.6で採用しない方針に変更 | SLP回路・R20.5メモリ案は残さない | 最終版の追加機能に数えない |
| R20.6 | 方針変更・互換処理 | R19.1基準へ戻し、拡張有効ED76をNOP化。拡張ロック時のIM1別名と通常HALTは維持。SLPと未定義命令TRAPを完成条件から除外 | 残る | EZ80NP6、MEM、RUNALL、ゲーム実機PASS |
| R21 | CPU命令追加 | INI2(ED84)、IND2(ED8C)、OUTI2(EDA4)、OUTD2(EDAC)。BC16bitポートを保持し、B−1、C±1、HL±1。HLの16/24bit対応。既存byte ALU/転送行を共用 | 残る | EZ80IO2。R21初版は実機停止、後のR21.2/R21.3で実機PASS |
| R21 | 診断追加 | 内部E6Hループバック、出力データとポート上位の署名を保持する8bitレジスタ。診断時は物理MSX IORQへ出さない | 残る | IO2の実機診断。外部周辺機器の電気的検証とは別 |
| R21.1 | デコード構造修正 | IO2用のグローバルopcode読替えMUXを除去。EDの該当行へ4opcodeを直接追加。Diag_Activeの感度リスト不足を明示修正 | 残る | ローカルの制御出力比較・回帰。R21.1時点では実機MEM FAILが残った |
| R21.2 | 観測機能追加 | ブリッジ受理時の書込み物理アドレス23bit＋データ8bitを31bit保持。読出しは既存ram_addr/resultを共用。診断F0〜F7で記録読出し | 記録回路は残る。読出し接続はR21.3で置換 | 実機MEM/IO2/RUNALL・ゲームPASS。MR3のCPU値は一致、W/Rはゼロ |
| R21.3 | 観測接続修正 | 記録のbyte選択をVerilogの定数caseへ移動。wrapperとTrace_Data 8bit / Trace_Select 4bitで明示接続。FD/FEで同じ8bit経路に55H/AAHを流す接続試験を追加 | 残る | EZ80MR4、MEM、IO2、RUNALL全PASS、ゲーム起動・PLAY |
| R21.3 | 文書更新 | 全97ニーモニックの実装状況、形式/suffix制限、残り工程、デコード構造、最悪Setup経路と遅延表 | 文書として追加 | doc/README.mdから参照 |

## R21.3での追加機能の要約

- ADL/MADL IM0対応（R19）。
- 幅prefix＋インデックスCBの正しい幅消費・割込み境界（R19.1の修正）。
- INI2 / IND2 / OUTI2 / OUTD2の4命令（R21）。
- 上記命令用の内部I/O診断と、拡張メモリ要求/返答の観測（R21〜R21.3）。
- 全体のデコードへ読み替えMUXを入れない構造と、観測接続の明示化（機能追加ではなく構造修正）。

SLPは「実装済み機能」には含めない。最終仕様は非対応NOP。
TRAPも実装していない。16bit I/Oポートの上位を00H固定する追加命令の除外も維持する。

## R19より前から存在するため、この期間の新規追加と数えないもの

24bitレジスタ/ALU/メモリアクセス、ADL命令フェッチ、JP/JR/CALL/RET、IM1/IM2/NMI、MBASE/MADLの基礎、MLT、LEA/PEA、TST、LDH/LDX試験群、通常/混在RST等。
これらにはR19以降の回帰・改善があっても、R19から初めて追加したとは表記しない。
LDH/LDXは試験群の名前であり、独立したeZ80ニーモニックではない。

## R21.3の実機・規模・未解決事項

ユーザー確認: EZ80MEM / EZ80IO2 / EZ80MR4 / RUNALL全項目PASS。SOFARUNからスペースマンボウ起動・PLAY。
Logic19439/20736=94%、LUT17208、ALU1877、Register7393/15915=47%。
R21.2比でLUT418減、Register31増。観測用last_writeの31bit保持FFは合成後にも残る。
最悪Setup−7.654ns、Hold−2.712nsで未達。元のメモリ不具合の原因と、R21.2の観測ゼロの厳密な原因は未確定。
実機PASS、観測症状の解消、タイミング収束は別の判定。

## 参照した配布資料

R19_README.md、R19_1_README.md、R20_6_README.md、R21_README.md、R21_1_README.md、R21_2_README.md、R21_3_README.md。
配布当時の「未確認」という記述は歴史的状態。現在の実機確認はこの資料とdoc/README.mdを優先する。
残る命令/形式はEZ80_INSTRUCTION_STATUS_R21_3.md、REMAINING_R21_3.md。
