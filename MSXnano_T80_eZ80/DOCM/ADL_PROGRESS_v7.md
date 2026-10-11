# v7: 24bit CALL/RETと独立した長いスタックの基盤

## 実装範囲
開発用FETCH24=trueに限り、5B付きCALL/RETを3バイト戻りアドレスの試験経路として実装。
これは完全なeZ80 CALL.LIL/RET.LILではない（後述）。

- SPL: 24bitの長いスタックポインタ。リセット値FFFFFF。
- 従来SP: 16bitでbank0。SPLと独立。
- 5B 31 ll mm hh: 開発用SPL初期化。通常の31 ll mmは従来SPを初期化。
- 5B CD ll mm hh: 24bitターゲットへのCALL。戻りPCを上位→中位→下位の順にSPLへpush。
- 5B C9: SPLから下位→中位→上位の順にpopし、24bit PCを復元。
- 5B付き条件CALL/RET: 8種類すべて。条件CALLの不成立時も3バイトのオペランドを消費。
- SPLは24bitで加減算・折返し、スタックアクセスのA24にも上位を出力。
- CALLターゲットの上位はTargetBankに保持。RETで得た上位はPCとA_BANKへ同時反映。
- 元T80/G80Aの8ファイルはSHA256一致。MSX用設定FETCH24=falseを保持。

## 検証
GHDL 155実行PASS: 従来59 + 新規96。
新規sim/tb_call24.vhdの試験プログラム・メモリモデルで確認。

| 項目 | 組合せ／確認 |
|---|---|
| 条件 | NZ/Z/NC/C/PO/PE/P/M、それぞれ成立・不成立 |
| WAIT | あり・なし |
| SPL初期値 | 030001 / 000001 / FF0001 |
| クロック | イネーブル1/16、入力捕捉を位相分離 |
| CALLオペランド | 01FFFF→020000をまたぐ3バイト読出し |
| 戻りPC | 境界をまたぐ020001、再CALLから020006へ復帰 |
| ネスト | 長いCALLの中で長いCALL、その中で短いCALL/RET |
| 短いSP | 9000を保ち、bank0の8FFF/8FFEに2バイト保存 |
| スタック境界 | 030000→02FFFF、000000→FFFFFF、FF0000→FEFFFF |
| 書込み | 2往復で16回、WAITによる重複なし、範囲外書込みなし、ガード未変更 |
| アドレス | A24下位=A、refreshはbank0 |

既存の互換・LD/STORE・割込み・JP・PC境界テストも再実行。
ログはtest_results_v7.log。

## マニュアルとの差と制限
Zilog UM007715-0415の混在モードCALL/RETは、戻りPCに加えて
02h/03hのモード情報をスタックに保存・復帰する。
本段階の5B CALL/RETはそのモード情報を保存せず、3バイトの戻りPCのみを扱う。
したがって既存のeZ80アセンブラが生成した一般的なCALL.LIL/RET.LILコードとの
互換性は未達。開発テスト専用の暫定経路として扱う。
ADL切替、MBASE、40/49/52を含む完全なsuffix幅制御、長いPUSH/POP、
LD SP,HLの長い形式、24bit実行からのIRQ/NMIとRETI/RETNは未実装。
高位バンク実行で割込みを有効にしない。旧モードの割込み回帰テストは通過。

## 実機と次段階
v7のGowin合成・実機動作は未確認。
MSX側A24の拡張メモリ接続はまだ未実装。FETCH24=trueの実機使用は不可。
既存EZ80V4.COM/EZ80DIAG.COMは旧機能の回帰用。
今回の新機能はsim/tb_call24.vhdで試験し、新しい実機用COMはまだない。

次はADLモードとモード情報付きスタックフレームを実装し、CALL/RETの
暫定経路をマニュアル準拠の経路へ置き換える。
その後24bitデータアクセス、MSXメモリ接続、割込み復帰、実機確認へ進む。
DOCMのメモリ割当とVDP読出し優先・CPU WAIT規則を継承する。

## 参照
Zilog eZ80 CPU User Manual UM007715-0415、Memory Mode SwitchingのCALL/RET表。
https://www.zilog.com/docs/UM0077.pdf
