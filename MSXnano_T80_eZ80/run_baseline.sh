#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p verification
cd verification
for f in t80_pack t80_reg t80_alu t80_mcode t80 g80a; do
 ghdl -a --std=08 -fsynopsys ../fpga/G80A/$f.vhd
done
for f in t80_pack t80_reg t80_alu t80_mcode t80 g80a; do
 ghdl -a --std=08 -fsynopsys ../fpga/G80A_eZ80/${f}_ez80.vhd
done
for tb in tb_baseline tb_ez80_baseline; do
 ghdl -a --std=08 -fsynopsys ../sim/$tb.vhd
 ghdl -e --std=08 -fsynopsys $tb
 for w in false true; do
  ghdl -r --std=08 -fsynopsys $tb -gINSERT_WAIT=$w --assert-level=error --vcd=${tb}_${w}.vcd
 done
done
ghdl -a --std=08 -fsynopsys ../sim/tb_upper.vhd
ghdl -e --std=08 -fsynopsys tb_upper
ghdl -r --std=08 -fsynopsys tb_upper --assert-level=error --vcd=upper.vcd

ghdl -a --std=08 -fsynopsys ../sim/tb_long_ld.vhd
ghdl -e --std=08 -fsynopsys tb_long_ld
for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_long_ld -gINSERT_WAIT=$w --assert-level=error --vcd=long_ld_${w}.vcd
done
python3 ../tools/check_long_ld.py long_ld_false.vcd long_ld_true.vcd

ghdl -a --std=08 -fsynopsys ../sim/tb_long_store.vhd
ghdl -e --std=08 -fsynopsys tb_long_store
for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_long_store -gINSERT_WAIT=$w --assert-level=error --vcd=long_store_${w}.vcd
done

ghdl -a --std=08 -fsynopsys ../sim/tb_hardware_com.vhd
ghdl -e --std=08 -fsynopsys tb_hardware_com
for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_hardware_com -gINSERT_WAIT=$w --assert-level=error
done

for tb in tb_v4_sparse tb_v4_irq; do
 ghdl -a --std=08 -fsynopsys ../sim/$tb.vhd
 ghdl -e --std=08 -fsynopsys $tb
 for w in false true; do
  ghdl -r --std=08 -fsynopsys $tb -gINSERT_WAIT=$w --assert-level=error
done
done

ghdl -a --std=08 -fsynopsys ../sim/tb_v4_diagnostic.vhd
for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_v4_diagnostic -gINSERT_WAIT=$w --assert-level=error
done

for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_v4_irq -gINSERT_WAIT=$w -gIRQ_AT_ADDR=256 --assert-level=error
done

ghdl -a --std=08 -fsynopsys ../sim/tb_pc24.vhd
for b in 0 1 255; do
 for w in false true; do
  ghdl -r --std=08 -fsynopsys tb_pc24 -gBOOT_BANK=$b -gINSERT_WAIT=$w --assert-level=error
 done
done
for w in false true; do
 ghdl -r --std=08 -fsynopsys tb_pc24 -gWIDE_FETCH=false -gBOOT_BANK=255 -gINSERT_WAIT=$w --assert-level=error
done
