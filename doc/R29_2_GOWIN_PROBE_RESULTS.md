# A～EのGOWIN実合成結果とR29.2

## 確認条件

ユーザー提供impl_A.zip、impl_B.zip、impl_C.zip、impl_D.zip、impl_E.zip。
GowinSynthesis V1.9.12.04 (89079)、GW2AR-LV18QN88C8/I7。5種類のprocess_configは同一。
AとBの配布ソースの差は、entityとpackage内componentのmeta_valid入力の既定値 `:= '0'` を外した2箇所だけ。

## 実ネットリストの結果

| 回路 | 結果 | LUT | Register | 判定FF |
| --- | --- | ---: | ---: | --- |
| A：既定値付き入力＋generic＋クロック内変数 | FAIL：02hの短い復帰でFAULT | 7 | 9 | 外部観測用のtag_s0は残るが、受け側は定数化 |
| B：入力の既定値のみ除去 | PASS：7168チェック | 11 | 13 | tag_s0、反転clkによる立下り捕捉 |
| C：Bからgenericも除去 | PASS：7168チェック | 11 | 13 | tag_s0、反転clkによる立下り捕捉 |
| D：9bitデータ＋判定一体化 | PASS：7168チェック | 11 | 13 | packet_reg_8_s0、反転clkによる立下り捕捉 |
| E：保持後に判定 | PASS：7168チェック | 11 | 12 | 独立判定FFなし。意図どおり |

各機能試験は全256データ×2入力元×2ストリーム幅と、捕捉停止・実行停止・捕捉後の入力変更を含む。
B～Dではtag_viewを逆にたどり、単一のDFFEへ届くことを構造検査で確認。CLKはclk_dをINVした信号、CEはcapture_d。
Eは保持後判定のため独立タグFF要件を課さない。
これは合成後のゼロ遅延機能試験と接続確認であり、Setup／Hold保証ではない。

## Aで起きていたこと

Aのprobe.vgではstate_view[0]のOBUF入力がVCC、state_view[1]～[3]のOBUF入力がGND。状態出力は0001（FAULT）に固定されている。
元の入力reset_n／execute／stream_longを変えても正常状態には移らない。判定入力が明示接続されているはずの受け側が、既定値0として扱われた場合と一致する合成結果。
合成ログにはframe_sink(predecode=true)を処理した後、NL0002のmodule sweptが記録され、frame_sinkは最終ネットリストに存在しない。警告単独ではなく、出力の定数化と機能試験のFAILを併せて評価する。
tag_s0 FFは外部tag_viewに出しているためAでも残る。実CPUのR29では判定値をCPU内部だけで使っていたため、受け側で使用されなくなると独立判定FFも不要として消えることを説明できる。

## 原因の範囲

この構成・GOWIN版では、既定値付き追加入力を持つcomponent接続で、明示した入力が合成結果に反映されない問題が再現した。
既定値を取り除くBだけで正常化するため、クロック内変数、boolean genericそのもの、判定FF一般、GSR、9bitバスの必要性を原因とする根拠はない。
component側とentity側の既定値を同時に除いた比較であり、どちらの既定値の内部処理が問題なのかまでは個別に分離していない。
全てのVHDL既定値付き入力や他のGOWIN版に同じ問題があるとは一般化しない。

## R29.2の実装

R29.1（FPGAソースはR28と同一）を動作基準として維持する。
R29.2はR29の前段判定保持を戻し、DI_FRAME_VALID入力から既定値を外す。t80_ez80.vhdのentity宣言とt80_pack_ez80.vhdのcomponent宣言が対象。
g80a_ez80.vhdの明示接続、データと判定の同時捕捉・同時保持、入力元の選択はR29と同じ。
9bit案は小規模試験でBと同じ11 LUT／13 Registerだったため、変更範囲を広げる根拠がない。CPUでは最小変更を選択する。
CPU単体を独自ラッパーへ接続する場合はDI_FRAME_VALIDを必ず明示接続する。INPUT_FRAME_PREDECODE=falseで前段判定を使わない場合も、DI_FRAME_VALID=>'0'等を明示する。
MSX用16bitバスと拡張24bitバスの分離、MBASE窓、FFFFh遮断、ブリッジ、SDRAM、VDP、SDC／CST、GPRJは変更しない。GSR利用は保留のまま。

## 統合後の確認

Bが単体で成功したことを、CPU全体の合成成功や実機成功と取り違えない。
check_gowin_cpu_r29_2.pyは実CPUネットリストに独立判定FFが存在し、CPUの復帰状態遷移へ接続されているかを確認する。
続いてframe_mode完了の境界条件で、256データ×2ストリーム幅×2判定bit条件=1024条件を確認する。正しい判定bitだけでなく、意図的に矛盾させた判定bitも与え、CPUが既定0や生データ再判定でなく、保持した判定を参照することを調べる。
FSMのone-hot符号やネット名等が変わった場合は、INCONCLUSIVEとして手動確認を要求する。単純な名前検索でFFが見つかっただけでPASSとはしない。
このチェッカーはCPU全体の命令実行、全到達状態の形式等価性、配置配線遅延を検証するものではない。境界条件はコードと結果JSONへ記録する。
過去の不良R29ネットリストを拒否し、R28基準の正常遷移を確認できることと、正常／欠落FF／反転判定の合成形式テスト用fixtureで検査能力を確認した。
R29.2のGOWIN使用量・Setup／Hold・実機結果は未確認。実implを確認してから実機へ適用する。
