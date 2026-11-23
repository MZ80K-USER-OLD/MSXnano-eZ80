# MBASEをMSX互換空間の選択に使う設計検討

`doc/MBASE_MSX_WINDOW_DESIGN_R25.md` を参照。

R25実機確認済みソースを調査した設計案です。R25のRTL・COM・bitstreamは変更していません。新しいCPU版や実装済みデバッグ機能を含む配布ではありません。

結論：全メモリアクセスの最終上位8bitとMBASEを比較したCPU出力を、ラッパーで要求アドレスと同時に保持する。I/O設定は有用だが、MBASE書込みの次値処理と、移動先PCを含むADL切替が必要。
