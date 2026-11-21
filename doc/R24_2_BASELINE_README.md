# MSXnano T80 eZ80 R24.2：レジスタペア読出しの一括コミット

R24.1の24bitレジスタI/Fへ、即値・絶対アドレス・間接／インデックス指定ロードの共通収集・一括書込みを追加した版です。
対象は拡張有効時のMode0。通常の拡張ロック中Z80動作は従来経路を維持します。

- LD rr,即値、LD IX/IY/SP,即値
- LD rr,(nn/Mmn)、LD IX/IY/SP,(nn/Mmn)
- LD rr,(HL)、LD rr,(IX+d)/(IY+d)、対応するIX/IY読出し

書込み先を保持し、2/3バイトを既存ワークへ収集して最後にまとめて更新します。
EX(SP)用24bitワークを共有し、新しい24bitデータ用FFは追加していません。
GSRは保留したままです。

詳細: [doc/R24_2_LOAD_COMMIT.md](doc/R24_2_LOAD_COMMIT.md)。
GOWINプロジェクト: `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`。
ZIP全体を新規フォルダへ展開し、R24/R24.1と同じ設定で合成・配置配線してください。

既存34本のCOM、RUNALL.BATは変更していません。新しいCOMのコピーは不要です。
最初にEZ80MEM /RUNを単独実行し、PASS後に次を確認してください。

```
EZ80D3 /RUN
EZ80MR4 /RUN
EZ80LDH /RUN
EZ80LDX /RUN
EZ80RW2 /RUN
EZ80RS8 /RUN
EZ80DEC /RUN
EZ80PFX /RUN
EZ80IM0 /RUN
RUNALL.BAT
```

テストの表示バージョンは元のままです。全PASS後、SOFARUNからスペースマンボウの起動・PLAYを確認します。
FAILならStage/ADDR/EXP/ACT、停止なら最後の表示を保存してください。
一括更新の内部タイミングはシミュレーションで検証し、実機では既存COMで命令結果を回帰確認します。

ローカル結果: verification_r24_2/summary.json。
再検証: python tools/verify_release_r24_2.py（GHDL/Icarus Verilogが必要）。
GOWINでの合成・配置後のLUT/FF/CLS・詳細タイミング、R24.2実機動作は未確認です。
R24.1の局所MUX見積り約96 LUTをR24.2全体の削減数として流用しないでください。
制御の共通化と追加した保持・コミット回路の差引を、実レポートで比較する必要があります。
