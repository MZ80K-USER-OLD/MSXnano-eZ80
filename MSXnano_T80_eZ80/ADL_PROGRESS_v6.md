# v6: 24bit JPターゲット転送

## 今回の実装
- 開発用FETCH24=trueの場合、5B C3 nn mm MMでPCに24bit絶対アドレスを転送。
- 5B付き条件JP（NZ/Z/NC/C/PO/PE/P/M）は、成立時に24bit転送、不成立時にも3バイトのオペランドを消費。
- 5B E9、5B DD E9、5B FD E9でHL/IX/IYの上位バイトを含めPCへ転送。
- 分岐先のA_BANKをPC変更と同じタイミングで更新。短いJPは現在のフェッチバンクを維持。
- 元T80/G80Aの8ファイルのSHA256一致。v4のsuffix途中の割込み抑制を継承。

Control_Longは今回のJP制御に用いる内部信号。完全な命令幅制御／ADLモードではない。
FETCH24=falseでは追加の24bit JP経路は無効で、従来の実機設定を継続する。

## 検証
GHDL 59実行PASS（従来27 + 今回32）。test_results_v6.logを参照。
新規sim/tb_jump24.vhd: 8条件 × 成立/不成立 × WAIT有/無。
各実行で絶対JP、HL/IX/IY経由JP、01FFFF→020000のオペランド境界、
短JPのバンク維持、refreshのbank0、AとA24下位の一致、意図しない書込みなしを検査。
クロックイネーブルは1/16、入力捕捉を位相分離。
既存の互換、長いLD/STORE、実機COM、割込み、PC境界テストも実行。

## 実機確認
2026-10-10: ユーザーから「スペースマンボウが正常に動いた」と報告。
この報告はv6変更前の実機結果。試験時間／ROMハッシュ／bitstreamハッシュは未取得。
v6のGowin合成と実機動作は未確認。
MSXプロジェクトはFETCH24=falseを保持し、A24は拡張メモリ未接続。
既存EZ80V4.COM / EZ80DIAG.COMは含むが、今回の24bit JPを検証する実機COMではない。
24bit分岐のテストプログラムとメモリモデルはsim/tb_jump24.vhdに含む。

## 限界と次段階
本段階は24bitターゲット転送の基盤で、完全なeZ80命令実装ではない。
5BによるADLモード切替は未実装。FETCH24はコンパイル時固定の開発設定。
40/49/52を含む一般的なsuffix幅制御、MBASE、短長スタック、24bit CALL/RET、
高位バンクでの割込み／復帰、24bitデータアクセスは未実装。
次は短長スタックとCALL/RETの設計・実装を進める。
その後MSXメモリ接続を実装し、実機で24bit機能をテストする。
メモリ接続時はDOCMのバンク割当とVDP読出し優先・CPU WAIT規則を参照。

## 参照
Zilog eZ80 CPU User Manual UM007715-0415:
https://www.zilog.com/docs/UM0077.pdf
JP.LILのオペコード／24bitターゲットを参照。マニュアルのADL遷移は本段階では未実装。
