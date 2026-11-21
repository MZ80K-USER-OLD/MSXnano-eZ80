# R11.9 検証結果

248条件と14条件の故障検出が合格。SD追加試験は8条件と2種類の故障検出。各条件で実CPUによるSD制御レジスタ読出し512回（LDIR含む）、直接全256番号読出し、拡張遮断510回を実行した。新旧のデータを実ラッパT3の捕捉エッジで比較し、書込み／選択状態を各clk_27mで比較した。通常／高速側の分周4/16、位相、WAIT、CEN停止を含む。

SD読出し番号の固定はoffset01h、上位4bit欠落はoffset10hで検出。SDシリアルカード通信やセクタ転送バッファ、Nextor／SofaRun全体のシミュレーションではない。

SD追加試験で用いた配布topを固定してから、Write比較8,388,608通り、実CPU回帰23群、CDC、EX(SP)、要求保持、実スロット回路の故障検出、ソース再生成・配布検査を完了した。CPUはR11.7と同じ。R11.7とのFPGA差分はtop_ez80.vのみ。先行COM20本、ラッパ、ブリッジ、SDRAM、VDP、SDC／CST／GPRJは未変更。

最終結果はverification_result.json、SD試験はverification_sd_r11_9_result.json、ソース・配布検査はverification_release_r11_9.json。再現入口はbash tools/run_checks.sh。

R11.9のGOWIN合成・配置配線・実機は未実行。遅延、Logic／LUT／CLS使用量は未測定。R11.7／R11.8のユーザー実機結果とレポートは基準情報として別記している。
