# v4: 24bit register stores into MSX low 64KB

Implemented: LD.LIS (nn),HL / IX / IY (49 22 lo hi; 49 DD/FD 22 lo hi).
Three bytes are written least significant first. Uses existing WAIT bus control.
LD.LIL immediate subset from v3 remains. Ordinary LD (nn),HL/IX/IY remains two bytes.
T80 original hashes unchanged. CPU selection and cpu1 hierarchy retained.

## Verification
11 GHDL executions PASS: baseline x4, upper register x1, long load x2,
long store x2, supplied COM x2. Normal and inserted WAIT covered.
VCD upper load checker also passes. COM test stubs BDOS; actual DOS not simulated.
The supplied COM compares full HL/IX/IY values, immediate PUSH/POP lower16,
ordinary LD/store and a guard byte. It prints EZ80 v4: PASS or FAIL.

## Hardware
Build fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj.
Copy hardware_test/EZ80V4.COM to SD and run EZ80V4 from MSX-DOS.
Only v4 supports the new store instruction; v3 must be replaced first.
Gowin synthesis and v4 hardware execution not tested here.
User has reported v3 lower16 hardware test PASS, and prior MSX/game operation.

## Limits
This remains a subset, not a full eZ80 CPU. PC and external addresses remain 16bit.
LIS stores implemented only for HL/IX/IY within bank0, without 64KB wrap.
No BC/DE/SP long stores, long memory reads, ADL mode, SPS/SPL or MBASE yet.
Do not use nonzero banks or boundary-crossing transfers.
49h is now a suffix rather than original Z80 LD C,C in the extended build.
5Bh already differs from Z80 LD E,E. Original T80 build preserves Z80 semantics.
Other suffix/instruction combinations and suffix interrupt edge cases are unverified.
Zilog reference: https://www.zilog.com/docs/UM0077.pdf
