# R37：LD A,I / LD A,Rのフラグ修正

R36基準。CPUの該当フラグ更新だけを修正しています。

詳細: [doc/R37_LD_A_IR_FLAGS.md](doc/R37_LD_A_IR_FLAGS.md)

新しい実機テスト: `EZ80IRF /RUN` → `EZ80IRF R37: PASS`

通常プロジェクト: `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

INI等の残件は未修正です。GOWIN・実機・タイミングは未確認。

---

以下は継承したR36以前の履歴です。

# R36：R33基準・復帰bit0判定比較版

R33のラッパー8bit入力FFを維持し、上位7bitの形式比較と判定FFを削除しました。
CPU内の既存復帰フレーム処理でbit0だけを判定します。R35の入力FF移動は含みません。

詳細: [doc/R36_RETURN_BIT0_FROM_R33.md](doc/R36_RETURN_BIT0_FROM_R33.md)

検証結果: [doc/R36_VALIDATION.json](doc/R36_VALIDATION.json)

通常GOWINプロジェクト: `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj`

COM30本とRUNALLは従来と同一です。GOWINタイミング・実機は未確認。

---

以下は継承したR33以前の履歴です。

# R33：ブロック命令の上位8bit更新経路を短縮

実機確認済みR32（Logic 80%、RUNALL全PASS、スペースマンボウPLAY）を基準に、ブロック命令の24bit増減結果を上位8bitまで伝搬させる経路を整理しました。下位16bitの境界だけを検出し、既存の上位8bit用増減器を共用します。カウンタのゼロ判定も加減算前の値から決定します。

命令のサイクル数とWAIT受付は維持します。変更RTLは `fpga/G80A_eZ80/t80_ez80.vhd` のみ。追加FF・パイプライン待ち・制約緩和はありません。

GOWINでは `fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj` をR32と別フォルダで再ビルドしてください。**R33のGOWIN使用率・タイミング・実機動作は未確認です。** 実測の改善量は配置配線レポートで比較します。

COMとRUNALLはR32と同じです。FLASHのテスト更新は不要です。

```
EZ80BLK /RUN
EZ80MEM /RUN
EZ80MR4 /RUN
RUNALL.BAT
```

全PASSと、SOFARUNからスペースマンボウの起動・PLAYを確認してください。COMの版表示は従来のままで正常です。

- 変更理由・算術・更新タイミング・残る経路：doc/R33_BLOCK_UPPER_PATH.md
- 検証結果：doc/R33_VALIDATION.json
- 検証ログ：doc/R33_evidence
- R32からの差分：R32_to_R33.patch
- 再検証：tools/verify_r33.py（Python3、GHDL、Icarus。GHDL／IVERILOG／IVL_ROOT／VVPを指定）

R32を機能比較・ロールバック基準として保持してください。R30は従来どおりタイミング比較用です。旧版名のdoc/toolsと検証集計は履歴です。
