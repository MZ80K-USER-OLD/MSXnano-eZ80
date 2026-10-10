# TA2003修正版

元v2のgenerateがgen_t80/gen_ez80という階層を追加し、SDCのcpu1指定と不一致になった。
今回top.v/top_ez80.vをプリプロセッサ選択に変更し、CPUを元と同じトップ直下のcpu1に配置。
SDCの18〜24行および対応hold制約を削除せず維持。
PSG env_resetのcreate_clock削除も含む。

Gowin用プロジェクトはproject_T80とproject_eZ80に分離したまま。
上位8bit追加を保持。元のG80A/T80はハッシュ一致。
条件分岐の静的確認で各topに選択したcpu1が1個だけ残ることを確認。
GHDL基準/WAIT/上位バイトの計5テストPASS。
Gowinの混在言語合成、配置配線、タイミング解析は未実行。
