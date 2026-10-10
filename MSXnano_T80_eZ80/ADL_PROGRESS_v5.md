# v5: 24bit PC and instruction-fetch address foundation

## Implementation
T80_eZ80 PC is now unsigned(23 downto 0).
FETCH24=false (default): PC arithmetic wraps at 16bit; upper byte stays zero.
FETCH24=true: sequential fetch and relative PC arithmetic use 24bit.
RESET_PC generic specifies a 24bit test boot address. Low16 remains the legacy A port.
Core A_BANK and G80A_eZ80 A24 provide the full fetch address.
Refresh and all data/I/O cycles use bank0 in this stage.
Legacy CPU, top hierarchy, SDC and project files remain unchanged.
The interrupt suffix fix from v4 is retained.

## Verification
27 GHDL executions PASS: previous19 plus8 boundary tests.
Sparse clock enables (1/16) and phase-separated input capture are used in boundary tests.
Long immediate HL load spans the boundary, followed by a 3byte store to bank0.
Cases with/without WAIT:
- 00FFFF -> 010000
- 01FFFF -> 020000
- FFFFFF -> 000000
- FETCH24=false: FFFF -> 0000, RESET_PC high byte ignored
Checks include full A24 address, its low16 equality with A, refresh bank0,
stored bytes 56 34 12, and no extra store outside the intended 3bytes.
Original T80/G80A hashes match the saved baseline.
Gowin synthesis and v5 hardware execution are NOT verified here.

## Hardware and limits
The MSX project still uses FETCH24=false and RESET_PC=000000.
A24 is not connected to MSX external memory, so do not enable FETCH24 on hardware yet.
Existing EZ80V4/EZ80DIAG programs are included unchanged as regression tests.
They verify v4 features, not 24bit instruction fetch.
User reported all diagnostic fields matching on v4 interrupt-fix hardware.

FETCH24 is a compile-time development setting, not ADL or a mode switch.
This is NOT full eZ80/ADL execution. No 24bit absolute jump/call/return yet.
Ordinary branches still fetch 16bit targets; high-bank interrupt/stack behavior is incomplete.
Do not run arbitrary eZ80 code with FETCH24=true.
24bit register-indirect data addressing, long memory reads, SPS/SPL, MBASE,
width suffix completion, and mode switching remain pending.
Next step: connect instruction/control width and 24bit target transfers,
then split short/long stack and add mixed-mode execution.
