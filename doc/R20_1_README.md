# R20.1 — SLP中のSDRAMリフレッシュ

R20を基準に、CPUがSLPでRFSHを止めてもSDRAMの更新要求を発行する処理を追加しました。SDRAM側の既存FreeCounterとCPU側の診断カウンタを共用します。CPU命令デコード・レジスタ・割り込み本体はR20と同一です。R20/R20.1のGOWIN・実機確認は未報告です。最後の実機確認済み基準はR19.1（Logic94%、LUT17182、ALU1877、全指定COM/RUNALL PASS、Space Manbow PLAY）です。

## 変更

- CPU_Sleepをラッパーからメモリコントローラへ接続し、108MHz側の2段同期後に使用。
- 既存FreeCounterは108MHzの1/4で加算されるため、下位8bitの256カウントをリフレッシュ周期として共用。108MHz動作なら約9.481µsごとに更新要求を保留。
- 実際のCPU用スロットへ進める境界で、従来CPU要求が非活動なら既存のrefreshステートを使用。VDP用スロットを使わない。スロット終端で待機している間は要求を消費しない。
- 保留中の拡張要求はペイロードを保持したまま次のCPU用スロットへ回す。従来mapper/megaram要求が活動している間は奪わない。
- cpu_sleep=0では追加要求が無効。既存のRFSH由来の更新条件、初期化コマンド、row/column/DQM、16/24bitアドレス分離を維持。

GOWINプロジェクトが参照する `fpga/top_ez80.v` の `SLEEP_REFRESH=1` 接続を使います。メモリモジュール単体の既定値は0で、旧インスタンスとの互換性を維持します。

新しい大きなカウンタは追加しません。RTL上の保持ビット追加は6個（メモリ側の同期2＋要求保留1、診断タイマーレベルの同期2＋前値1）。CPUのアーキテクチャ上の状態ビットは増やしません。LUT/FFの実際の増減はGOWIN未測定です。

通常SLPの解除は引き続きRESETのみです。今回の自律更新は、SDRAM/VDP側のクロックが動作し続け、CPUがSLPでバスを解放している場合を対象にします。システムクロック全停止、SLP以外の長時間BUSRQ、発振器停止、RTC/WDT省電力機構は追加していません。温度・電圧を含む実機での保持保証やSTA収束を確認した結果ではありません。

## 新規実機テスト

```text
EZ80REF /RUN
```

期待表示：`EZ80REF R20.1: PASS`

`hardware_test/EZ80REF.COM` とプロジェクト直下に収録。3401バイト、CRC32 `2DDB339C`。R20のCOM29本は変更せず、新規1本を加えた30本をテストZIPにまとめています。

Z80/ADLの2ケースで、MADL=1・保留IRQの状態からSLPへ入り、長時間の診断専用解除後にAF・SPS/SPL・完了記録と、次のデータを確認します。

| 24bitアドレス | 期待値 |
|---|---|
| 030000 | 96 |
| 03FFFF | C9 |
| 07FFFE | 31 |
| 07FFFF | 52 |
| 080000 | A6 |
| 0EFFFF | 5A |

VDPアクセスが一部行の保持に寄与する可能性もあるため、COMのPASSだけでREFRESHコマンドの発行周期を証明したとは扱いません。周期と全バンクの論理検査は専用試験で確認します。

失敗はStage・ADDR・EXP・ACTで表示します。これらの私有領域とコード/結果の0A:6000/7000/8000/8100および0E:8200、SPL=05:0001近傍を上書きします。MSX/DOSベクタやVRAM/MegaRAM予約枠は書き換えません。

長時間解除には新しい診断コマンドD7を使います。既存FreeCounter[15]の立ち上がりを2段同期し、既存の4bit診断カウンタ15回を2巡します。108MHzなら約70.4〜72.8msのSLPになり、64msを超えます。CPUはこの間RFSHを出しません。D3の短時間解除と既存EZ80SLP.COMは維持します。

D7は診断専用で、通常のSLP復帰条件ではありません。F0=01/F1=FEが新しい識別値です。旧版はNOT READY、診断無効はNOT READY、拡張無効はUNSUPPORTED、/RUNなしはREADYとしてSLPへ進みません。指定GPRJを使ってください。CPUだけを別のtopへ移した場合はSleep_Timer/CPU_Sleepの接続が必要です。

DOS/BIOSがEIすることを考慮し、試験中はシステムコールを行いません。復帰時はDI、Z80/MBASE=0、MADL=0、元のDOSスタック、IM1、診断停止・拡張ロックへ戻します。DOS表示後にもDIしてIX/IYを戻し、EIして終了します。

## ビルド・実機確認

R20.1を新しいフォルダへ展開し、同じ `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をビルドしてください。R20を先に実機確認する必要はありません。

1. Logic、LUT/ALU/FF、CLS、Setup/Hold結果を記録。
2. `EZ80MEM /RUN`、`EZ80RW2 /RUN`。
3. `EZ80REF /RUN`、`EZ80SLP /RUN`。
4. `EZ80PFX /RUN`、`EZ80IM0 /RUN`、`EZ80RS8 /RUN`、`RUNALL.BAT`。
5. SofaRunでスペースマンボウを起動してPLAY。

RUNALL.BATは既存のままなので、REF/SLP等は別途実行します。古いimpl/bitstreamは含めません。GPRJ・DualPin・SystemVerilog設定・CST・SDCは変更していません。false path/multicycle/max-delayの追加・緩和もありません。

## ローカル検証

結果は `verification_r20_1/summary.json` に集約します。

- RFSH=1固定での自律更新、4種類の要求発生位相、VDPの連続読み出し、拡張CPU要求の保持・完了と全4バンク/全byte laneの読み書きを照合。
- 100MHzの保守的な試験クロックで約83.9ms実行し、8192回の更新を確認。更新間隔と4096回のローリング時間窓を監視。機能モデル上で最大間隔10.24µs、4096回/64msの条件を確認。refresh抑止の故障が検査で検出されることも確認。
- `EZ80REF.COM` の実バイトをCPU＋ブリッジ＋SDRAMモデルで実行。通常/WAIT・CEN停止/故障検出/READY/UNSUPPORTED/NOT READYを検査。COM実行シミュレーションでは解除タイマの入力をFreeCounter[7]へ接続し256倍速めます。実際の70ms停止をCOMシミュレーションで再現したとは扱いません。メモリ側の長時間更新は別の約83.9ms試験で検査します。
- MEM、RW2、D3/CTL、IM0、PFX、SLP、NMI診断、CDC、ロック中互換性、VHDL-93を回帰。通常モードは追加機能を有効にしたうえでcpu_sleep=0を与え、従来SDRAMとのピン比較も行います。
- 新しいtopのCPU/メモリ/ブリッジ接続を部分的にエラボレーション。その他のIPはブラックボックスで、全システムの合成やシミュレーションではありません。

SDRAMモデルは論理コマンド/データモデルで、電荷漏れ・温度・電圧・全JEDECタイミングを再現しません。リフレッシュ要求の不足を修正したことと、実機で長時間データ保持を確認したことを区別してください。今回のFPGA変更はラッパー、memory_ez80.v、top_ez80.vの3ファイルです。CPU本体の命令実装とマイクロデコーダはR20と同一で、以前の全ISA試験を新規実行として数えません。

一次資料：[Gowin GW2AR Data Sheet DS226](https://cdn.gowinsemi.com.cn/DS226E.pdf)、SDR SDRAMは64Mbit/32bit、4096 refresh cycles/64ms。既存のrefreshコマンド列を共用しており、新しい電気的タイミングの合否は未確認です。
