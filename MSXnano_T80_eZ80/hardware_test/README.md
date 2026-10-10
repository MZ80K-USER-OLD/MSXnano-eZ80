# 実機テスト

v4拡張CPUでGowin合成・書込み後、EZ80V4.COMをSDへコピーしMSX-DOSでEZ80V4を実行。
成功表示: EZ80 v4: PASS。失敗表示: EZ80 v4: FAIL。
v3や元T80ではこのテストを実行しない。

HL=123456h、IX=667788h、IY=99AABBhをロードして3バイト保存し全バイトを比較。
24bitロード直後の通常PUSH HL/POP DEで3456hを確認。
通常LD HL,ABCDhと2バイト保存を確認し、保存先の3バイト目が0のままかを比較。
SPの差分や割込み、上位バイト保持の全命令仕様はこのCOMの対象外。
ソースは正確な機械語をDEFBで表現。build_test.pyでソースとCOMを再生成できる。
BDOS呼出しはGHDLではスタブを使用。実際のMSX-DOS上のv4動作は未確認。
