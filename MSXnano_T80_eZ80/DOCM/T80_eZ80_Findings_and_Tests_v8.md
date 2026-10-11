# T80/eZ80調査結果とテスト一覧（v8時点）

## 結論
ここまでの試験で、元T80固有の潜在不良と確定できるものは見つかっていない。
確認された不具合は追加したeZ80 suffixの割込み受付処理であり、元T80の不良ではない。
元T80/G80Aの8ファイルは保存済みSHA256と一致。元CPUには修正していない。
これは全命令・全条件の正常性の証明ではない。全面的なFUSE検証やBIOS起動から
ゲームまでのGHDL比較、全割込みモード・NMI投入試験は未完了。

## 実機確認
2026-10-11、ユーザー報告: v8でスペースマンボウが起動し、PLAYできた。
前回のv7ではSofaRunからの起動を確認。
この結果はFETCH24=falseのMSX互換経路の実機確認。24bit PC/CALL/RET/SPLは
MSXメモリ未接続で、実機確認済みとは扱わない。
プレイ時間・ゲーム全クリア・ROM/bitstreamハッシュは未取得。

## 不具合と注意事項
| 分類 | 内容 | 根拠・状態 | 対応／テスト |
|---|---|---|---|
| eZ80追加部分の確認済み不具合 | 49h/5Bh直後にINTを受け付け、pending suffixをISR内で消費 | 旧v4の49h境界INTでHL保存が56 34 00、期待56 34 12をGHDLで再現 | v4 irqfix以降、suffixと本体の間のINT/NMI受付を保留。tb_v4_irq.vhd |
| eZ80追加部分の制御上の潜在問題 | v7の長いCALLでM7が従来のIX/IY補助サイクル終了経路へ流れる構造 | ソース確認で発見。v7の通常試験は通っており、実機不良の直接原因とは未確認 | v8で長いCALLのM7を独立制御。tb_call24.vhd |
| 実機FAILの原因未確定 | 初期EZ80V4でFAIL、上位バイト00。その後診断値一致 | 最初のFAILを割込み不良または異なるbitstreamと断定する証拠は不足 | EZ80DIAGのDI/EI結果と書込bitstreamを記録して切り分け |
| eZ80拡張による命令解釈の変更 | 49h/5BhはZ80ではLD C,C / LD E,Eだが、拡張CPUではsuffix | 設計上の差異。任意のZ80バイナリについて完全互換とは言えない | 元T80プロジェクトを保持。ゲーム動作確認だけでは全面検証にならない |
| 未実装機能 | 動的ADL、02h復帰、MBASE、混在suffix、高位バンクIRQ/NMI、一般的な24bitデータアクセス | v8は開発用固定幅、03hフレームのみ | 未実装を潜在不良と混同しない。後続実装と専用試験が必要 |

NMIはsuffix保留条件を修正したが、tb_v4_irqはINT投入のみ。
高位バンクで割込みを有効にする試験はまだ行っていない。
以前のFAIL_INVESTIGATION.mdは当時の記録で、そこにある「実機未確認」は当時の状態。
現在の実機確認結果は本書を参照。

## 実機用テスト
| ファイル | 実行 | 確認範囲 |
|---|---|---|
| hardware_test/EZ80V4.COM | MSX-DOSでEZ80V4 | 24bit即値HL/IX/IY、3バイト保存、通常PUSH/POPと短いLD/STORE。EZ80 v4: PASS / FAIL |
| hardware_test/EZ80DIAG.COM | MSX-DOSでEZ80DIAG | DI/EIブロックのHL/IX/IY、PUSH、短い保存、SP前後を表示 |

v8のeZ80プロジェクトで使用可能。元T80プロジェクトでは実行しない。
COMをSDへコピーしてMSX-DOSのプロンプトから実行する。
EZ80DIAGの期待値（下位→上位）:
HL=56 34 12、IX=88 77 66、IY=BB AA 99、PUSH=56 34、SHORT=CD AB 00。
SP0とSP1は一致。DI/EI両方を確認し、間欠的失敗の切り分けには繰返し実行。
診断結果一致は測定時の一致で、任意タイミングのIRQ/NMIの証明ではない。
ASMソース: ez80_test_v4.asm / ez80_diagnostic.asm。
再生成: hardware_testで python3 build_test.py / python3 build_diagnostic.py。
実機COMはv4相当の拡張確認用。v5〜v8の高位アドレス機能のテストではない。

## GHDL用テスト
| ファイル | 主な確認内容 |
|---|---|
| sim/tb_baseline.vhd / tb_ez80_baseline.vhd | 元T80と拡張CPUの基本回帰（限定された試験プログラム） |
| sim/tb_v4_irq.vhd | 49h/5Bh境界でINT投入、WAIT・疎なクロック |
| sim/tb_v4_diagnostic.vhd / tb_hardware_com.vhd | COMの計算・保存結果。BDOSはスタブ |
| sim/tb_pc24.vhd | フェッチの64KB/24bit折返し、通常・WAIT |
| sim/tb_jump24.vhd | 全8条件のJP、HL/IX/IY、短JPのバンク維持 |
| sim/tb_call24.vhd | 03h＋戻りPCの4バイトフレーム、ネスト、独立SP、境界、20回の書込み |

プロジェクト直下で bash run_baseline.sh（GHDLとPython3が必要）。
v8で155実行PASS。test_results_v8.logを同梱。
試験プログラムは各VHDLテストベンチのROM定義に含まれる。
新しい実機用24bitテストはメモリ接続後にASM/COMとして作成する。
