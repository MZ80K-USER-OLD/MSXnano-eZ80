# R23.1 — R21.3へ戻したI/O削除比較版

2026-11-21。基準は実機でMR4/MEM/IO2/RUNALLのPASSとSOFARUNからスペースマンボウのPLAYが報告されたR21.3。R22.4やR23から不要回路を削り戻した版ではなく、保存済みR21.3のFPGA SHA-256一覧と一致するソースから作成した。

## 今回の範囲

| 命令・機能 | R23.1の扱い |
|---|---|
| INI2 / IND2 / OUTI2 / OUTD2（ED84/8C/A4/AC） | 削除。EDページのNOP行へ移動 |
| INI2R / IND2R / OTI2R / OTD2R | R21.3には未実装。そのままNOP |
| INIRX / INDRX / OTIRX / OTDRX / TSTIO | 今回は追加しない。安定確認後の別工程 |
| 通常Z80のIN / OUTとブロックI/O・反復版 | 維持 |
| その他のeZ80追加I/O | 除外方針を維持 |
| SLP / 未定義命令TRAP | SLPはNOP、TRAPは実装しない |

R23で実装したTSTIO等は持ち込まない。これは必要な5命令を完成させた版ではなく、追加を止めて削除だけの影響を実機で比較する版。

変更したFPGAファイルは次の4本だけ。

- `t80_pack_ez80.vhd`: IO2の書込みクラスCを削除。
- `t80_mcode_ez80.vhd`: IO2専用分岐、M4/M5でのB/C別更新、6サイクル指定を削除。通常Z80の行を維持。
- `t80_ez80.vhd`: Block_IO2判定、専用フラグ処理、通常処理を抑止する条件を削除。
- `g80a_ez80.vhd`: 旧IO2対応識別F8/F9を00/FFへ変更。旧EZ80IO2を誤実行させない。

4ファイル以外のFPGAファイルはR21.3とバイト一致。メモリブリッジ、SDRAM制御、top、16bit/24bitバス分離、トレースMUX、GPRJ、CST、SDCを維持する。MBASEに連動したMSX窓、24bit加算器統一、R22以降のWAIT監視・パイプライン観測・I/O反復制御を持ち込まない。

メモリ観測はR21.3のMR4を使用。MR6/MX6はこの版には対応しないため同梱しない。MR4の識別FB/FC=03/FCは維持し、COMも変更していない。

## 実機用テスト

新規 `hardware_test/EZ80ION.COM` を同梱し、ルートにも同じファイルを置く。

```
EZ80ION /RUN
```

正常時はCASE 0〜7の後に `EZ80ION R23.1: PASS`。4命令×Z80/ADLの8ケースで、AF/BC/DE/HLとSPS/SPLが変化しないことを検査する。命令は拡張RAM上で実行する。幅指定別・DD/FD組合せの全形式を網羅するCOMではない。

DOS/BIOSがEIする前提で、表示時にはZ80/MBASE0・拡張ロックに戻し、DOSから戻った直後にDI。呼出元IX/IYとSPSを復元し、MSXベクタやセカンダリスロットのFFFFHには書き込まない。メモリ比較失敗時はADDR/EXP/ACTを表示する。

COMは14730 bytes、CRC32 **89950529**。削除対応識別F8/F9を検査し、旧IO2対応版ではNOT READYとなる。R23等の同じ削除識別を持つ版も受理するため、ビットストリームの厳密な版識別の代用にはしない。

従来の32本のCOMはバイト不変。EZ80IO2は履歴として残すが、この版ではNOT READYが正常。RUNALLからIO2を外し、IONを追加した。旧READMEや古い検証資料は履歴であり、今回の実行手順は本資料を優先する。

## GOWIN・実機の手順

1. ZIPを新規フォルダへ展開する。
2. **`fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`** を開き、合成から配置配線まで実行する。古いimplは同梱しない。
3. 生成したイメージを書き込み、電源再投入する。
4. `EZ80MEM /RUN` → `EZ80MR4 /RUN` → `EZ80ION /RUN` → `RUNALL.BAT` の順で確認する。MEM/MR4で不一致が出た場合は以降の結果を合格判定に使わず、画面を保存する。
5. SOFARUNからスペースマンボウを起動してPLAYを確認する。
6. Logic/CLS/RegisterとSetup/Holdを記録する。Logic削減量は今回の再合成結果で判断する。

期待表示:

```
EZ80MEM P1: PASS
EZ80MR4 R21.3: PASS
EZ80ION R23.1: PASS
```

本版のGOWIN合成、配置配線後タイミング、実機動作、回路規模は未確認。R21.3の実機PASSはSTA収束の証明ではなく、削除後に同じ配置になる保証もない。

## ローカル検証

実際に再実行した結果は `verification_r23_1/summary.json` と同梱ログを参照。

- デコード比較: Mode 0〜3、各458752入力。R21.3との比較で意図した4命令の拡張ED実行条件のみを除外。他ページ・拡張ロック・割込み条件を含む。
- 削除NOP: 通常/WAIT・CE停止、Z80/ADL・幅指定、160ケース。既にNOPだった4反復opcodeも含み、I/O発生なし、レジスタ不変を検査。
- EZ80MEM実COM: 9条件。正常4位相、故障注入4条件、拡張無効。
- EZ80MR4実COM: 8条件。通常、CE停止、故障、拡張無効、/RUNなし、旧識別、観測接続故障等。
- EZ80ION実COM: 7条件。通常、CE停止、故障注入、拡張無効、/RUNなし、旧機能識別、診断無効。DOSのEIとIM1割込みをモデル化。
- VHDL-93: 6ファイル解析。

故障注入・NOT READY等は期待した終了であり、すべてが実機PASSという意味ではない。GHDLから生成したCPUとブリッジ/SDRAMモデルでの検証であり、GOWINの配置配線遅延、Nextor/VDP全体は再現していない。

再実行は `python tools/verify_release_r23_1.py`。GHDL/Icarusを環境変数GHDL/GHDL_PREFIX/IVERILOG/IVL_ROOT/VVPで指定できる。旧版のverifyスクリプトには削除前IO2を期待するものがあり、本版の合否には使わない。

今後はこの版で実機安定性と規模を確認してから、残す5命令を分割して追加する。制約の一律緩和は行わない。
