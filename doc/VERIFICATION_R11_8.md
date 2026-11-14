# R11.8 検証結果

240条件のシミュレーションと12条件の故障検出が合格。Write比較はMode 0～3の4条件、合計8,388,608通りで全49出力を照合。分類を壊した時のWrite不一致も検出した。

最終RTLを固定してから、Write比較、実CPU回帰23群、CDC、EX(SP)ワークレジスタ、要求保持・隔離、実スロット回路の故障検出、ソース再生成・配布検査を実行した。実CPU回帰の途中にFPGAソースの変更は行っていない。

R11.7からのFPGA変更はt80_mcode_ez80.vhdだけ。元のLegacy_Writeと他48出力のデコードは維持し、MCycle非依存の命令条件と共通サイクル条件で追加命令Writeを生成する。IRとWrite_Classの保持、ラッパ、top、ブリッジ、SDRAM、VDP、SDC／CST／GPRJ、先行COM20本は未変更。

最終結果はverification_result.json。比較結果はverification_write_r11_8_result.json、配布検査はverification_release_r11_8.json、各テストのログはverification_logs。再現入口はbash tools/run_checks.sh。

GOWIN合成・配置配線・実機は未実行。タイミング改善、LUT／Logic／CLS使用量は未測定。R11.7の実機PASSと実測レポートは基準情報として別記している。
