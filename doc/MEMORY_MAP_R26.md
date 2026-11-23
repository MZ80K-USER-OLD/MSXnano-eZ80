# R26 SD-RAMメモリマップ

## 物理バイトアドレス

| SD-RAM物理範囲 | 容量 | 用途 |
|---|---:|---|
| 000000h～3FFFFFh | 4 MiB | MSXメモリマッパRAM |
| 400000h～5FFFFFh | 2 MiB | MegaRAM |
| 600000h～63FFFFh | 256 KiB | VRAM予約。VDP本体の既存I/Fは17bit・128KiBで、予約だけでは256KiB表示機能にならない |
| 640000h～64FFFFh | 64 KiB | 拡張bank 00h。R26でprivate RAMデコードを有効化 |
| 650000h～7FFFFFh | 1728 KiB | 拡張bank 01h～1Bh |

640000h～7FFFFFhはbank00h～1Bhの28×64KiBに対応する。R25ではこのうち640000h～64FFFFhを普通の拡張アクセスから使えなかった。物理容量を追加する変更ではない。

## CPUから見える24bit空間

通常メモリでは、先に **アドレス上位8bit＝MBASE** を判定し、一致なら下位16bitをMSXバスへ送る。MSX空間はスロット／サブスロット／マッパで選択され、単一の連続したSD-RAM 64KiBではない。ROMや周辺機器も含む。

非一致の場合のみ、次の拡張デコードを使用する。

| CPUのbank | 拡張側の用途 | 物理変換 |
|---|---|---|
| 00h～1Bh | private RAM | 640000h＋CPUアドレス |
| 40h～5Fh | MegaRAM | CPUアドレス下位23bit |
| 60h～63h | VRAM予約 | `{5'b11000, A[15:0], A[17:16]}`。VDPのlane配置に合わせて並べ替える |
| その他 | 未割当 | FFh読出し／書込み無視。未割当だけを理由にWAITし続けない |

MBASEが上記割当のbankに一致した場合、その64KiB分はMSX窓を優先する。例えばMBASE=0Ehなら、0E0000h～0EFFFFhはMSX窓となり、対応するprivate RAM物理720000h～72FFFFhは普通のアクセスから隠れる。

リセットはMBASE=00h、ADL=0なので従来どおりMSX起動。MBASE=FFhならFF0000h～FFFFFFhがMSX窓となり、000000h～00FFFFhは拡張private RAMとなる。

I/Oは窓判定とは別の16bit経路。IACK／refreshも既存の資格処理を維持する。非一致xxFFFFhはMSX16=0000h／MSX MREQ無効で隔離する。FFFFhだけを比較するセカンダリスロット回路へ漏らさない。一致bankのFFFFhはMSXの通常仕様に従う。

診断有効時のベクタ読出しには専用overrideがある。これは通常マップの例外で、R26_MBASE_MSX_WINDOW.mdを参照。

VRAM共有アクセスは既存のVDP優先・競合時CPU WAITを維持する。今回、SD-RAM仲裁やVDP自体は変更していない。
