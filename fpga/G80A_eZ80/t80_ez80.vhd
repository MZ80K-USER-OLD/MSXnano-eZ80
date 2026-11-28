--
-- Z80 compatible microprocessor core
--
-- Version : 0250_T80 (+k04)
--
-- Copyright (c) 2001-2002 Daniel Wallner (jesus@opencores.org)
--
-- All rights reserved
--
-- Redistribution and use in source and synthezised forms, with or without
-- modification, are permitted provided that the following conditions are met:
--
-- Redistributions of source code must retain the above copyright notice,
-- this list of conditions and the following disclaimer.
--
-- Redistributions in synthesized form must reproduce the above copyright
-- notice, this list of conditions and the following disclaimer in the
-- documentation and/or other materials provided with the distribution.
--
-- Neither the name of the author nor the names of other contributors may
-- be used to endorse or promote products derived from this software without
-- specific prior written permission.
--
-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
-- AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
-- THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
-- PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE
-- LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
-- CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
-- SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
-- INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
-- CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
-- ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
-- POSSIBILITY OF SUCH DAMAGE.
--
-- Please report bugs to the author, but before you do so, please
-- make sure that this is not a derivative work and that
-- you have the latest version of this file.
--
-- The latest version of this file can be found at:
--  http://www.opencores.org/cvsweb.shtml/T80_eZ80/
--
-- Limitations :
--
-- File history :
--
--  0208 : First complete release
--  0210 : Fixed wait and halt
--  0211 : Fixed Refresh addition and IM 1
--  0214 : Fixed mostly flags, only the block instructions now fail the zex regression test
--  0232 : Removed refresh address output for Mode > 1 and added DJNZ M1_n fix by Mike Johnson
--  0235 : Added clock enable and IM 2 fix by Mike Johnson
--  0237 : Changed 8080 I/O address output, added IntE output
--  0238 : Fixed (IX/IY+d) timing and 16 bit ADC and SBC zero flag
--  0240 : Added interrupt ack fix by Mike Johnson, changed (IX/IY+d) timing and changed flags in GB mode
--  0242 : Added I/O wait, fixed refresh address, moved some registers to RAM
--  0247 : Fixed bus req/ack cycle
--  0248 : Added undocumented DDCB and FDCB opcodes by TobiFlex 2010.04.20
--  0249 : Added undocumented XY-Flags for CPI/CPD by TobiFlex 2012.07.22
--  0250 : Added R800 Multiplier by TobiFlex 2017.10.15
--
--  +k01 : Version alignment by KdL 2010.10.25
--  +k02 : Added R800_mode signal by KdL 2018.05.14
--  +k03 : Version alignment by KdL 2019.05.20
--  +k04 : Separation of T800 from T80_eZ80 by KdL 2021.02.01
--

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.T80_eZ80_Pack.all;

entity T80_eZ80 is
    generic(
        Mode        : integer := 0;  -- 0 => Z80, 1 => Fast Z80, 2 => 8080, 3 => GB
        DATA_EXTENDED : boolean := true;
        IOWait      : integer := 0;  -- 0 => Single I/O cycle, 1 => Std I/O cycle
        Flag_C      : integer := 0;
        Flag_N      : integer := 1;
        Flag_P      : integer := 2;
        Flag_X      : integer := 3;
        Flag_H      : integer := 4;
        Flag_Y      : integer := 5;
        Flag_Z      : integer := 6;
        Flag_S      : integer := 7
    );
    port(
        RESET_n     : in std_logic;
        CLK_n       : in std_logic;
        CEN         : in std_logic;
        WAIT_n      : in std_logic;
        INT_n       : in std_logic;
        NMI_n       : in std_logic;
        BUSRQ_n     : in std_logic;
        M1_n        : out std_logic;
        IORQ        : out std_logic;
        NoRead      : out std_logic;
        Write       : out std_logic;
        RFSH_n      : out std_logic;
        HALT_n      : out std_logic;
        BUSAK_n     : out std_logic;
        A           : out std_logic_vector(15 downto 0);
        A_BANK : out std_logic_vector(7 downto 0);
        MADL_State : out std_logic;
        MBASE_State : out std_logic_vector(7 downto 0);
        A_MSX_MATCH : out std_logic; -- final address bank equals current MBASE
        Extension_State : out std_logic;
		update_addr	: out std_logic;
        DInst       : in std_logic_vector(7 downto 0);
        DI          : in std_logic_vector(7 downto 0);
        DO          : out std_logic_vector(7 downto 0);
        MC          : out std_logic_vector(2 downto 0);
        TS          : out std_logic_vector(2 downto 0);
        IntCycle_n  : out std_logic;
        IntE        : out std_logic;
        Stop        : out std_logic
    );
    -- GOWIN SUG550: avoid a clocked BSRAM ROM on the CPU control path.
    attribute syn_romstyle : string;
    attribute syn_romstyle of T80_eZ80 : entity is "logic";
end T80_eZ80;

architecture rtl of T80_eZ80 is

    signal Address_Reg : std_logic_vector(15 downto 0);
    signal Address_Bank_Reg, Data_Out_Reg : std_logic_vector(7 downto 0);
    signal Write_Decode : std_logic;
    signal Branch_Condition : std_logic;
    signal Decode_Flags : std_logic_vector(7 downto 0);
    constant aNone  : std_logic_vector(2 downto 0) := "111";
    constant aBC    : std_logic_vector(2 downto 0) := "000";
    constant aDE    : std_logic_vector(2 downto 0) := "001";
    constant aXY    : std_logic_vector(2 downto 0) := "010";
    constant aIOA   : std_logic_vector(2 downto 0) := "100";
    constant aSP    : std_logic_vector(2 downto 0) := "101";
    constant aZI    : std_logic_vector(2 downto 0) := "110";

    -- R1: PC and SPS stay 16-bit. No ADL execution/interrupts in this stage.
    signal MADL : std_logic;
    type frame_state_type is (frame_idle, frame_push, frame_vector, frame_mode, frame_long, frame_upper, frame_short, frame_fault);
    signal Frame_State : frame_state_type;
    signal Frame_TS : unsigned(2 downto 0);
    signal Frame_Count : integer range 0 to 3;
    signal Frame_Mode_Bit, Frame_IM2, Frame_RetN : std_logic;
    signal Frame_Calling, Frame_Is_Call, Frame_SPS, Frame_Take, Frame_Target_Last : std_logic;
    signal Frame_Rst, Frame_Rst_Ready, Frame_Destination_Long : std_logic;
    signal Frame_Rst_Pending : std_logic; -- R18.3: request decoded at fetch T3, before the T4 start gate.
    signal Frame_Stack_Short, Frame_Stack_Down : std_logic;
    signal Frame_Stack_Value, Frame_Stack_Delta, Frame_Stack_Next : unsigned(23 downto 0);
    signal Frame_Stack_Bank : std_logic_vector(7 downto 0);
    signal Frame_Active, Frame_Ready, Frame_Start, Frame_Unsupported, Frame_Entry, Frame_Return, Frame_End, Frame_Returning, Frame_IEF, CPU_Run : std_logic;
    signal NoRead_Base : std_logic;
    signal MBASE : std_logic_vector(7 downto 0);
    -- R24.1: register data crosses the module boundary as complete 24-bit words.
    signal Reg24A, Reg24B, Reg24C, Reg24DI : std_logic_vector(23 downto 0);
    -- Comparison candidate: share pair/HL selection without adding FFs.
    signal Pair_Raw_Index, HL_Resolved_Index, XY_Register_Index : std_logic_vector(2 downto 0);
    signal Reg24Mask, Reg24AddrU, Reg24AddrW : std_logic_vector(2 downto 0);
    signal Reg24UpperU : std_logic_vector(7 downto 0);
    signal Reg24Exchange : std_logic;
    signal Upper_View : std_logic_vector(63 downto 0);
    signal Upper_Port_Events : std_logic_vector(7 downto 0);
    signal Upper_Port_WE : std_logic;
    signal Upper_Port_Index : std_logic_vector(2 downto 0);
    signal Upper_Port_Data, Upper_Inc_Byte, Upper_Immediate_Byte : std_logic_vector(7 downto 0);
    function Upper_Mask(v : std_logic_vector; en : std_logic) return std_logic_vector is
        variable result : std_logic_vector(v'range);
    begin
        result:=(others=>'0');if en='1' then result:=v;end if;return result;
    end function;

    signal Wide_Stack, Wide_IncDec : std_logic;
    signal Write_Class : std_logic_vector(7 downto 0);
    signal Exec_Control : exec_control_t;
    signal Exec_Normal : std_logic;
    signal Stack_Upper_Index : std_logic_vector(2 downto 0);
    signal Pair_Indirect, Pair_Indexed, Indirect_Read, Indirect_Opposite : std_logic;
    signal Indirect_Offset : integer range 0 to 1;
    signal Indirect_Index, Pair_Commit_Index : std_logic_vector(2 downto 0);
    signal Pair_Absolute, Pair_Read, Pair_SP : std_logic;
    -- R24.2: EX_SP_Read is the shared 24-bit collection work register.
    signal Load_Active, Load_Commit, Load_Three, Load_SP : std_logic;
    signal Load_Target : std_logic_vector(2 downto 0);
    signal Load_First, Load_Last : unsigned(2 downto 0);
    signal Load_Result : std_logic_vector(23 downto 0);
    signal Load_Mask : std_logic_vector(2 downto 0);
    signal Pair_Number : std_logic_vector(1 downto 0);
    signal Pair_Upper_Index : std_logic_vector(2 downto 0);
    signal Pair_Address_Last : integer range 3 to 4;
    signal Byte_Absolute, EX_SP_Long, EX_SP_Result_WE : std_logic;
    signal EX_SP_Index : std_logic_vector(2 downto 0);
    signal EX_SP_Read, EX_SP_Source : std_logic_vector(23 downto 0);
    signal EX_SP_Address, EX_SP_Address_Next : unsigned(23 downto 0);
    signal Arith_Long, Arith_Commit, Arith_Sub, Arith_Carry : std_logic;
    signal Arith_Target, Arith_Source : std_logic_vector(2 downto 0);
    signal Arith_Left, Arith_Right : unsigned(23 downto 0);
    signal Arith_Flags : std_logic_vector(7 downto 0);
    signal Arith_Sub_Latched, Arith_Carry_Latched, Arith_Is_ADD : std_logic;
    signal Arith_Xor_Right : unsigned(23 downto 0);
    signal Arith_Sum : unsigned(24 downto 0);
    signal Arith_Result : unsigned(23 downto 0);
    signal Arith_Overflow, Arith_Half, Arith_Carry_Out : std_logic;
    signal Block_Instruction, Block_Long, Instruction_Has_Width, Block_IO2 : std_logic;
    signal Pair_Low_Wrap, Block_Result_Zero : std_logic;
    signal Mul_Active, Mul_Commit, Mul_Reg_Commit : std_logic;
    signal Mul_Target : std_logic_vector(2 downto 0);
    signal Mul_Operand : unsigned(15 downto 0);
    signal Mul_Left, Mul_Right : unsigned(7 downto 0);
    signal Mul_Product : unsigned(15 downto 0);
    attribute syn_dspstyle : string;
    attribute syn_dspstyle of Mul_Product : signal is "dsp";
    signal EA_Active, PEA_Active, PEA_Long, LEA_Commit : std_logic;
    signal EA_Source, EA_Target, RegAddrC_Base : std_logic_vector(2 downto 0);
    signal EA_Result : std_logic_vector(23 downto 0);
    signal ADL_Mode, JP_Immediate, JP_Commit : std_logic;
    signal Ctrl_Stack, Ctrl_Call, Ctrl_Ret, Ctrl_Rst, Ctrl_Taken, Flow_Cond : std_logic;
    signal Ctrl_Target, Ctrl_Return : std_logic_vector(23 downto 0);
    signal IRQ_Long, IRQ_Return, IRQ_IM2, IRQ_IM0, Effective_IEF, IV_Read_Commit : std_logic;
    signal IRQ_Vector : unsigned(23 downto 0);
    signal I_Upper : std_logic_vector(7 downto 0);
    signal NMI_Accept : std_logic;
    signal SPL : unsigned(23 downto 0);
    signal Extensions_Enabled, Unlock_Armed : std_logic;
    signal Width_Pending, Data_Long, Stream_Long : std_logic;
    signal Width_Code : std_logic_vector(7 downto 0);
    signal Index_Bank : std_logic_vector(7 downto 0);
    signal SP_Readback : std_logic;
    signal Indexed_Address : signed(23 downto 0);
    signal Load_Upper_Index : std_logic_vector(2 downto 0);
    -- Registers
    signal ACC, F           : std_logic_vector(7 downto 0);
    signal Ap, Fp           : std_logic_vector(7 downto 0);
    signal I                : std_logic_vector(7 downto 0);
    signal R                : unsigned(7 downto 0);
    signal SP : unsigned(15 downto 0);
    signal PC, PC_Increment : unsigned(23 downto 0);
    signal RegDIH           : std_logic_vector(7 downto 0);
    signal RegDIL           : std_logic_vector(7 downto 0);
    signal RegBusA          : std_logic_vector(15 downto 0);
    signal RegBusB          : std_logic_vector(15 downto 0);
    signal RegBusC          : std_logic_vector(15 downto 0);
    signal RegAddrA_r       : std_logic_vector(2 downto 0);
    signal RegAddrA         : std_logic_vector(2 downto 0);
    signal RegAddrB_r       : std_logic_vector(2 downto 0);
    signal RegAddrB         : std_logic_vector(2 downto 0);
    signal RegAddrC         : std_logic_vector(2 downto 0);
    signal RegWEH           : std_logic;
    signal RegWEL           : std_logic;
    signal Alternate        : std_logic;

    -- Help Registers
    signal TmpAddr          : std_logic_vector(15 downto 0);    -- Temporary address register
    signal IR               : std_logic_vector(7 downto 0);     -- Instruction register
    signal Base_Group : base_group_t;
    signal CB_Group : cb_group_t;
    signal ED_Group : ed_group_t;
    signal ISet             : std_logic_vector(1 downto 0);     -- Instruction set selector
    signal RegBusA_r        : std_logic_vector(15 downto 0);

    signal ID16             : signed(15 downto 0);
    signal Save_Mux         : std_logic_vector(7 downto 0);

    signal TState           : unsigned(2 downto 0);
    signal MCycle           : std_logic_vector(2 downto 0);
    signal IntE_FF1         : std_logic;
    signal IntE_FF2         : std_logic;
    signal Halt_FF          : std_logic;
    signal BusReq_s         : std_logic;
    signal BusAck           : std_logic;
    signal ClkEn            : std_logic;
    signal NMI_s            : std_logic;
    signal INT_s            : std_logic;
    signal IStatus          : std_logic_vector(1 downto 0);

    signal DI_Reg           : std_logic_vector(7 downto 0);
    signal T_Res            : std_logic;
    signal XY_State         : std_logic_vector(1 downto 0);
    signal Pre_XY_F_M       : std_logic_vector(2 downto 0);
    signal NextIs_XY_Fetch  : std_logic;
    signal XY_Ind           : std_logic;
    signal No_BTR           : std_logic;
    signal BTR_r            : std_logic;
    signal Auto_Wait        : std_logic;
    signal Auto_Wait_t1     : std_logic;
    signal Auto_Wait_t2     : std_logic;
    signal IncDecZ          : std_logic;

    -- ALU signals
    signal BusB             : std_logic_vector(7 downto 0);
    signal BusA             : std_logic_vector(7 downto 0);
    signal ALU_Q            : std_logic_vector(7 downto 0);
    signal F_Out            : std_logic_vector(7 downto 0);

    -- Registered micro code outputs
    signal Read_To_Reg_r    : std_logic_vector(4 downto 0);
    signal Arith16_r        : std_logic;
    signal Z16_r            : std_logic;
    signal ALU_Op_r         : std_logic_vector(3 downto 0);
    signal ALU_cpi_r        : std_logic;
    signal Save_ALU_r       : std_logic;
    signal PreserveC_r      : std_logic;
    signal MCycles          : std_logic_vector(2 downto 0);

    -- Micro code outputs
    signal MCycles_d        : std_logic_vector(2 downto 0);
    signal TStates          : std_logic_vector(2 downto 0);
    signal IntCycle         : std_logic;
    signal NMICycle         : std_logic;
    signal Inc_PC           : std_logic;
    signal Inc_WZ           : std_logic;
    signal IncDec_16        : std_logic_vector(3 downto 0);
    signal Prefix           : std_logic_vector(1 downto 0);
    signal Read_To_Acc      : std_logic;
    signal Read_To_Reg      : std_logic;
    signal Set_BusB_To      : std_logic_vector(3 downto 0);
    signal Set_BusA_To      : std_logic_vector(3 downto 0);
    signal ALU_Op           : std_logic_vector(3 downto 0);
    signal ALU_cpi          : std_logic;
    signal Save_ALU         : std_logic;
    signal PreserveC        : std_logic;
    signal Arith16          : std_logic;
    signal Set_Addr_To      : std_logic_vector(2 downto 0);
    signal Jump             : std_logic;
    signal JumpE            : std_logic;
    signal JumpXY           : std_logic;
    signal Call             : std_logic;
    signal RstP             : std_logic;
    signal LDZ              : std_logic;
    signal LDW              : std_logic;
    signal LDSPHL           : std_logic;
    signal IORQ_i           : std_logic;
    signal Special_LD       : std_logic_vector(2 downto 0);
    signal ExchangeDH       : std_logic;
    signal ExchangeRp       : std_logic;
    signal ExchangeAF       : std_logic;
    signal ExchangeRS       : std_logic;
    signal I_DJNZ           : std_logic;
    signal I_CPL            : std_logic;
    signal I_CCF            : std_logic;
    signal I_SCF            : std_logic;
    signal I_RETN           : std_logic;
    signal I_BT             : std_logic;
    signal I_BC             : std_logic;
    signal I_BTR            : std_logic;
    signal I_RLD            : std_logic;
    signal I_RRD            : std_logic;
    signal I_INRC           : std_logic;
    signal SetDI            : std_logic;
    signal SetEI            : std_logic;
    signal IMode            : std_logic_vector(1 downto 0);
    signal Halt             : std_logic;
    signal XYbit_undoc      : std_logic;

    function decode_branch(
                F : std_logic_vector(7 downto 0);
                cc : bit_vector(2 downto 0)
                ) return boolean is
        begin
                if Mode = 3 then
                        case cc is
                        when "000" => return F(7) = '0'; -- NZ
                        when "001" => return F(7) = '1'; -- Z
                        when "010" => return F(4) = '0'; -- NC
                        when "011" => return F(4) = '1'; -- C
                        when "100" => return false;
                        when "101" => return false;
                        when "110" => return false;
                        when "111" => return false;
                        end case;
                else
                        case cc is
                        when "000" => return F(6) = '0'; -- NZ
                        when "001" => return F(6) = '1'; -- Z
                        when "010" => return F(0) = '0'; -- NC
                        when "011" => return F(0) = '1'; -- C
                        when "100" => return F(2) = '0'; -- PO
                        when "101" => return F(2) = '1'; -- PE
                        when "110" => return F(7) = '0'; -- P
                        when "111" => return F(7) = '1'; -- M
                        end case;
                end if;
        end;
    function PC_Width(value : unsigned(23 downto 0); wide : std_logic) return unsigned is
        variable v : unsigned(23 downto 0);
    begin
        v:=value;if wide='0' then v(23 downto 16):=(others=>'0');end if;return v;
    end function;begin
    Frame_Active<='0' when Frame_State=frame_idle else '1';
    Frame_Entry<='1' when MADL='1' and (IntCycle='1' or NMICycle='1') else '0';
    Frame_Take<='1' when Write_Class(0)='0' else Branch_Condition;
    Frame_Calling <= Exec_Control(EC_FRAME_CALL) and Exec_Normal;
    Frame_Return <= ((Exec_Control(EC_FRAME_IRQ_RET) and MADL) or (Exec_Control(EC_FRAME_RET) and Frame_Take)) and Exec_Normal;
    Frame_Target_Last<='1' when (Frame_Count=1 and Stream_Long='0' and IRQ_IM0='0') or Frame_Count=2 else '0';
    -- R18: RST reuses the call-like frame writer, but has no immediate target.
    -- For RST, the first suffix letter chooses the destination mode.
    Frame_Rst <= Exec_Control(EC_FRAME_RST) and Exec_Normal;
    Frame_Rst_Ready <= Frame_Rst when Exec_Control(EC_RST_WIDTH_OK)='1' or (Exec_Control(EC_EXPLICIT_WIDTH)='0' and MADL='1') else '0';
    Frame_Destination_Long<='1' when IRQ_IM0='1' else Data_Long when Frame_Rst='1' else Stream_Long;
    -- Noncanonical full suffixes retain the guarded, no-stack-change behavior.
    Frame_Unsupported <= Frame_Rst and Exec_Control(EC_RST_WIDTH_BAD);
    Frame_Ready<='1' when Extensions_Enabled='1' and Frame_State=frame_idle and MCycle="001" and TState=4 and
        (Frame_Entry='1' or Frame_Return='1' or Frame_Calling='1' or Frame_Rst_Pending='1') else '0';
    -- R18.3: canonical and guarded RST forms both need a frame start.
    -- Their union is simply RST and (explicit width or MADL); the width
    -- comparison remains in the dispatch, outside the normal CPU run gate.
    -- IR/width state is accepted at fetch T2 and is stable at accepted T3.
    -- Hold through CEN gaps, WAIT and BUSRQ; consume at fetch T4 as before.
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then Frame_Rst_Pending<='0';
        elsif rising_edge(CLK_n) then
            if CEN='1' and Frame_End='1' then Frame_Rst_Pending<='0';
            elsif ClkEn='1' and MCycle="001" and TState=3 then
                Frame_Rst_Pending<=(Frame_Rst and (Instruction_Has_Width or MADL)) or IRQ_IM0;
            end if;
        end if;
    end process;
    Frame_Start<=Frame_Ready and not BusAck;
    CPU_Run<=CEN and not Frame_Active and not Frame_Start;
    Frame_Returning<='1' when Frame_State=frame_mode or Frame_State=frame_long or Frame_State=frame_upper or Frame_State=frame_short else '0';
    Frame_End<='1' when Frame_TS=3 and
        ((Frame_State=frame_push and Frame_SPS='0' and Frame_IM2='0' and
          (Frame_Count=0 or (IRQ_IM0='1' and MADL='0' and Frame_Count=1))) or
         (Frame_State=frame_mode and IRQ_IM0='1') or
         (Frame_State=frame_vector and ((Frame_Is_Call='0' and Frame_Count=2) or (Frame_Is_Call='1' and Frame_Target_Last='1' and Frame_Take='0'))) or
         (Frame_State=frame_long and ((Frame_Mode_Bit='0' and Frame_Count=1) or Frame_Count=2)) or
         (Frame_State=frame_short and Frame_Count=1)) else '0';
    Frame_IEF<=IntE_FF2 when Frame_Returning='1' and Frame_RetN='1' else IntE_FF1 when Frame_Returning='1' or Frame_Is_Call='1' else '0';
    -- One carry chain for both stack widths and both push/pop directions.
    -- SPS wraps at 16 bits; its bank comes from MBASE, never from carry-out.
    Frame_Stack_Short<='1' when Frame_State=frame_short or (Frame_State=frame_idle and Frame_Rst_Ready='1' and Frame_Destination_Long='0') or
        (Frame_State=frame_push and Frame_SPS='1' and Frame_Count=2) or
        (Frame_State=frame_vector and Frame_Is_Call='1' and Frame_Destination_Long='0') else '0';
    Frame_Stack_Down<='1' when Frame_State=frame_push or
        (Frame_State=frame_vector and Frame_Is_Call='1') or Frame_Entry='1' or (Frame_State=frame_idle and (Frame_Rst_Ready='1' or IRQ_IM0='1')) else '0';
    Frame_Stack_Value<=resize(SP,24) when Frame_Stack_Short='1' else SPL;
    Frame_Stack_Delta<=(others=>'1') when Frame_Stack_Down='1' else to_unsigned(1,24);
    Frame_Stack_Next<=Frame_Stack_Value+Frame_Stack_Delta;
    Frame_Stack_Bank<=MBASE when Frame_Stack_Short='1' else std_logic_vector(Frame_Stack_Next(23 downto 16));
    -- R13.1: both engines drive the shared registered bus payload.
    A<=Address_Reg;
    A_BANK<=Address_Bank_Reg;
    MBASE_State <= MBASE;
    A_MSX_MATCH <= '1' when Address_Bank_Reg=MBASE else '0';
    MADL_State <= MADL;
    DO<=Data_Out_Reg;
    Write<='1' when Frame_State=frame_push and Frame_TS/=4 else '0' when Frame_Active='1' else Write_Decode;
    NoRead<='1' when Frame_Active='1' and (Frame_TS=4 or Frame_State=frame_fault or (Frame_State=frame_mode and IRQ_IM0='1')) else '0' when Frame_Active='1' else NoRead_Base;
    -- The previous instruction's delayed flag write completes at fetch T1.
    -- Capture at accepted fetch T2, alongside IR, and hold for the instruction.
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then Decode_Flags <= (others=>'1');Branch_Condition<='0';
        elsif rising_edge(CLK_n) then
            if ClkEn='1' and MCycle="001" and TState=2 and WAIT_n='1' then
                Decode_Flags <= F;
                if decode_branch(F,to_bitvector(DInst(5 downto 3))) then Branch_Condition<='1';else Branch_Condition<='0';end if;
            end if;
        end if;
    end process;

    mcode : T80_MCode_eZ80
        generic map(
            Mode => Mode,
            Flag_C => Flag_C,
            Flag_N => Flag_N,
            Flag_P => Flag_P,
            Flag_X => Flag_X,
            Flag_H => Flag_H,
            Flag_Y => Flag_Y,
            Flag_Z => Flag_Z,
            Flag_S => Flag_S)
        port map(
            IR => IR, Write_Class=>Write_Class,
            Base_Group=>Base_Group, CB_Group=>CB_Group, ED_Group=>ED_Group,
            Exec_Control=>Exec_Control, Interrupt_Long=>IRQ_Long,
            Ext_Active=>Exec_Control(EC_EXT), Data_Long=>Data_Long, Stream_Long=>Stream_Long, ADL_Mode=>Exec_Control(EC_ADL_SNAPSHOT), Has_Width=>Exec_Control(EC_EXPLICIT_WIDTH), Flow_Cond=>Flow_Cond, Branch_Condition=>Branch_Condition, Interrupt_Mode=>IStatus,
            ISet => ISet,
            MCycle => MCycle,
            F => Decode_Flags,
            NMICycle => NMICycle,
            IntCycle => IntCycle,
            XY_State => XY_State,
            MCycles => MCycles_d,
            TStates => TStates,
            Prefix => Prefix,
            Inc_PC => Inc_PC,
            Inc_WZ => Inc_WZ,
            IncDec_16 => IncDec_16,
            Read_To_Acc => Read_To_Acc,
            Read_To_Reg => Read_To_Reg,
            Set_BusB_To => Set_BusB_To,
            Set_BusA_To => Set_BusA_To,
            ALU_Op => ALU_Op,
            ALU_cpi => ALU_cpi,
            Save_ALU => Save_ALU,
            PreserveC => PreserveC,
            Arith16 => Arith16,
            Set_Addr_To => Set_Addr_To,
            IORQ => IORQ_i,
            Jump => Jump,
            JumpE => JumpE,
            JumpXY => JumpXY,
            Call => Call,
            RstP => RstP,
            LDZ => LDZ,
            LDW => LDW,
            LDSPHL => LDSPHL,
            Special_LD => Special_LD,
            ExchangeDH => ExchangeDH,
            ExchangeRp => ExchangeRp,
            ExchangeAF => ExchangeAF,
            ExchangeRS => ExchangeRS,
            I_DJNZ => I_DJNZ,
            I_CPL => I_CPL,
            I_CCF => I_CCF,
            I_SCF => I_SCF,
            I_RETN => I_RETN,
            I_BT => I_BT,
            I_BC => I_BC,
            I_BTR => I_BTR,
            I_RLD => I_RLD,
            I_RRD => I_RRD,
            I_INRC => I_INRC,
            SetDI => SetDI,
            SetEI => SetEI,
            IMode => IMode,
            Halt => Halt,
            NoRead => NoRead_Base,
            Write => Write_Decode,
            XYbit_undoc => XYbit_undoc);

    alu : T80_ALU_eZ80
        generic map(
            Mode => Mode,
            Flag_C => Flag_C,
            Flag_N => Flag_N,
            Flag_P => Flag_P,
            Flag_X => Flag_X,
            Flag_H => Flag_H,
            Flag_Y => Flag_Y,
            Flag_Z => Flag_Z,
            Flag_S => Flag_S)
        port map(
            Arith16 => Arith16_r,
            Z16 => Z16_r,
            ALU_cpi => ALU_cpi_r,
            ALU_Op => ALU_Op_r,
            IR => IR(5 downto 0),
            ISet => ISet,
            BusA => BusA,
            BusB => BusB,
            F_In => F,
            Q => ALU_Q,
            F_Out => F_Out);

    -- R30: execution uses instruction-static descriptor predicates.
    Exec_Normal <= not (IntCycle or NMICycle);
    Load_Active<=(Exec_Control(EC_LOAD_IMM) or Exec_Control(EC_LOAD_ABS) or Exec_Control(EC_LOAD_IND)) and Exec_Normal;
    -- Data_Long/Stream_Long are already registered with the instruction.
    Load_Three<=Stream_Long when Exec_Control(EC_LOAD_IMM)='1' else Data_Long;
    Load_Commit<=Load_Active when unsigned(MCycle)=Load_Last and TState=3 else '0';
    -- Bypass the final accepted byte to the commit port: no extra T-state.
    Load_Result<=DI_Reg & EX_SP_Read(15 downto 0) when Load_Three='1' and Data_Long='1' else
                 x"00" & EX_SP_Read(15 downto 0) when Load_Three='1' else
                 x"00" & DI_Reg & EX_SP_Read(7 downto 0);
    Load_Mask<=(Data_Long or (Exec_Control(EC_LOAD_IMM) and Stream_Long)) & "11";

    Pair_Raw_Index<=Alternate & IR(5 downto 4);
    XY_Register_Index<=XY_State(1) & "11";
    HL_Resolved_Index<=XY_Register_Index when XY_State/="00" else Alternate & "10";
    Load_Upper_Index<=HL_Resolved_Index when Exec_Control(EC_PAIR_HL)='1' else Pair_Raw_Index;
    Indexed_Address<=signed(Reg24C)+resize(signed(DI_Reg),24);
    Wide_Stack <= Exec_Control(EC_STACK) and Exec_Normal;
    Wide_IncDec <= Exec_Control(EC_INCDEC) and Exec_Normal;
    Stack_Upper_Index<=Load_Upper_Index;
    Pair_Absolute <= Exec_Control(EC_PAIR_ABS) and Exec_Normal;
    -- R16: no extra work register, FSM state, byte counter or ALU.
    Pair_Indirect <= Exec_Control(EC_PAIR_IND) and Exec_Normal;
    Pair_Indexed <= Exec_Control(EC_PAIR_INDEX) and Exec_Normal;
    Indirect_Offset<=1 when Pair_Indexed='1' else 0;
    Indirect_Opposite<=Exec_Control(EC_IND_OPPOSITE);
    Indirect_Read<='1' when Write_Class(7 downto 4)=x"B" else '0';
    Indirect_Index<=(Indirect_Opposite xor (XY_State(1) and Pair_Indexed)) & "11" when Exec_Control(EC_PAIR_SP)='1' else Alternate & IR(5 downto 4);
    Pair_Commit_Index<=Indirect_Index when Pair_Indirect='1' else Pair_Upper_Index;
    EX_SP_Address_Next<=EX_SP_Address+1;
    Pair_Read<=IR(3);
    Pair_Number<="10" when Exec_Control(EC_PAGE_BASE)='1' else IR(5 downto 4);
    Pair_SP<=Exec_Control(EC_ABS_SP);
    Pair_Upper_Index<=HL_Resolved_Index when Pair_Number="10" else Alternate & Pair_Number;
    Pair_Address_Last<=4 when Stream_Long='1' else 3;
    Byte_Absolute <= Exec_Control(EC_BYTE_ABS) and Exec_Normal;
    EX_SP_Long <= Exec_Control(EC_EX_SP) and Exec_Normal;
    EX_SP_Index<=HL_Resolved_Index;
    EX_SP_Result_WE<='1' when EX_SP_Long='1' and MCycle="111" and TState=3 else '0';
    -- Address work register advances only after an accepted T2.
    -- M1/T3 prepares the first read before the M1/T4 address latch.
    Arith_Long <= Exec_Control(EC_ARITH) and Exec_Normal;
    Arith_Target<=HL_Resolved_Index when Exec_Control(EC_PAGE_BASE)='1' else Alternate & "10";
    Arith_Source<=Arith_Target when Exec_Control(EC_PAIR_HL)='1' else Pair_Raw_Index;
    Arith_Sub<=Exec_Control(EC_PAGE_ED) and not IR(3);
    Arith_Carry<=F(Flag_C) and Exec_Control(EC_PAGE_ED);
    Arith_Commit<='1' when Arith_Long='1' and MCycle="001" and TState=7 else '0';
    -- Both operands and flags are captured at T4 and held through the T7 commit.
    -- Addition and subtraction share this single adder; subtraction complements B.
    Arith_Xor_Right<=not Arith_Right when Arith_Sub_Latched='1' else Arith_Right;
    Arith_Sum<=resize(Arith_Left,25)+resize(Arith_Xor_Right,25)+to_unsigned(1,25) when (Arith_Carry_Latched xor Arith_Sub_Latched)='1'
        else resize(Arith_Left,25)+resize(Arith_Xor_Right,25);
    Arith_Result<=Arith_Sum(23 downto 0);
    Arith_Half<=Arith_Left(12) xor Arith_Right(12) xor Arith_Result(12);
    Arith_Carry_Out<=Arith_Sum(24) xor Arith_Sub_Latched;
    Arith_Overflow<=(not (Arith_Left(23) xor Arith_Right(23) xor Arith_Sub_Latched)) and (Arith_Left(23) xor Arith_Result(23));
    Block_Instruction <= Exec_Control(EC_BLOCK) and Exec_Normal;
    Block_Long<=Block_Instruction and Data_Long;
    Block_IO2 <= Exec_Control(EC_IO2) and Exec_Normal;
    -- R33: upper-byte updates use a lower16 boundary test and the shared
    -- 8-bit incrementer. No low16 carry chain feeds the upper data input.
    Pair_Low_Wrap<='1' when (IncDec_16(3)='1' and RegBusA=x"0000") or
        (IncDec_16(3)='0' and RegBusA=x"FFFF") else '0';
    -- The increment/decrement result is zero only at these two inputs.
    Block_Result_Zero<='1' when (IncDec_16(3)='1' and Reg24A=x"000001") or
        (IncDec_16(3)='0' and Reg24A=x"FFFFFF") else '0';
    Mul_Active <= Exec_Control(EC_MUL) and Exec_Normal;
    Mul_Target<=Pair_Raw_Index;
    Mul_Operand<=SPL(15 downto 0) when Exec_Control(EC_PAIR_SP)='1' and Data_Long='1' else
        SP when Exec_Control(EC_PAIR_SP)='1' else unsigned(RegBusA);
    Mul_Commit<='1' when Mul_Active='1' and MCycle="001" and TState=7 else '0';
    Mul_Reg_Commit<=Mul_Commit when Exec_Control(EC_PAIR_SP)='0' else '0';
    EA_Active <= Exec_Control(EC_EA) and Exec_Normal;
    PEA_Active <= Exec_Control(EC_PEA) and Exec_Normal;
    PEA_Long<=PEA_Active and Data_Long;
    EA_Source<="111" when Exec_Control(EC_EA_SOURCE_IY)='1' else "011";
    EA_Target<="011" when Exec_Control(EC_EA_TARGET_IX)='1' else "111" when Exec_Control(EC_EA_TARGET_IY)='1' else Alternate & IR(5 downto 4);
    LEA_Commit<='1' when EA_Active='1' and PEA_Active='0' and MCycle="010" and TState=5 else '0';
    RegAddrC<=XY_State(1) & "11" when Pair_Indexed='1' else Alternate & "10" when Pair_Indirect='1' else EA_Source when EA_Active='1' else RegAddrC_Base;
    PC_Increment<=PC+1;
    JP_Immediate <= Exec_Control(EC_JP) and Exec_Normal;
    JP_Commit<='1' when JP_Immediate='1' and (Exec_Control(EC_JP_ALWAYS)='1' or Flow_Cond='1') and TState=3 and
        ((Stream_Long='1' and MCycle="100") or (Stream_Long='0' and MCycle="011")) else '0';
    -- Acknowledge exactly at the dispatch boundary; Address_Reg new edge at that same
    -- clock wins in the input latch and remains pending for Address_Reg subsequent entry.
    NMI_Accept<='1' when (Frame_End='1' and NMI_s='1') or (Frame_Active='0' and Frame_Start='0' and NMI_s='1' and Prefix="00" and Width_Pending='0' and BusReq_s='0' and T_Res='1' and NextIs_XY_Fetch='0' and
        not ((MCycle="111" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0') or
             (MCycle="110" and Mode=1 and ISet/="01" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0')) and
        (MCycle=MCycles or No_BTR='1' or (MCycle="010" and I_DJNZ='1' and IncDecZ='1'))) else '0';
    -- R19: IM0 in ADL/MADL uses the shared frame engine. Locked/ordinary
    -- Z80 IM0 retains the original T80 peripheral-instruction path.
    IRQ_IM0<='1' when Mode=0 and Extensions_Enabled='1' and IntCycle='1' and NMICycle='0' and
        IStatus="00" and (ADL_Mode='1' or MADL='1') else '0';
    IRQ_Long <= Extensions_Enabled and ADL_Mode and (IntCycle or NMICycle);
    IRQ_IM2 <= '1' when IRQ_Long='1' and IntCycle='1' and IStatus="10" else '0';
    IRQ_Return <= Exec_Control(EC_IRQ_RETURN) and Exec_Normal;
    Effective_IEF <= '1' when ADL_Mode='1' and SetEI='1' else IntE_FF2 when IRQ_Return='1' and Exec_Control(EC_RETN_OPCODE)='1' and MCycle="100" else IntE_FF1;
    IV_Read_Commit <= Exec_Control(EC_IV_READ) and Exec_Normal when MCycle="001" and TState=4 else '0';
    Ctrl_Stack <= '1' when IRQ_Long='1' or IRQ_Return='1' else Exec_Control(EC_NATIVE_CTRL) and Exec_Normal;
    Ctrl_Call<=Ctrl_Stack when IRQ_Long='0' and IRQ_Return='0' and Exec_Control(EC_CALL_KIND)='1' else '0';
    Ctrl_Ret<='1' when IRQ_Return='1' else Ctrl_Stack when IRQ_Long='0' and Exec_Control(EC_RET_KIND)='1' else '0';
    Ctrl_Rst<='1' when IRQ_Long='1' else Ctrl_Stack when IRQ_Return='0' and Exec_Control(EC_RST_KIND)='1' else '0';
    Ctrl_Taken<='1' when IRQ_Return='1' or Exec_Control(EC_UNCOND_FLOW)='1' or Ctrl_Rst='1' else Flow_Cond;
    Extension_State<=Extensions_Enabled;
    SP_Readback <= Exec_Control(EC_SP_READ);
    ClkEn <= CPU_Run and not BusAck;

    T_Res <= '1' when TState = unsigned(TStates) else '0';

    NextIs_XY_Fetch <= '1' when XY_State /= "00" and XY_Ind = '0' and
                            ((Set_Addr_To = aXY) or
                            (MCycle = "001" and Exec_Control(EC_INDEX_FETCH)='1')) else '0';

    Save_Mux <= BusB when ExchangeRp = '1' else
        DI_Reg when Save_ALU_r = '0' else
        ALU_Q;

    -- R11.10: ordinary upper-byte commits share one combinational write port.
    -- These eight events belong to disjoint opcode families. No pipeline
    -- stage is added: the original enabled rising edge performs the commit.
    -- Mode0 pair reads now use the common final commit, including the upper byte.
    Upper_Port_Events(0)<='1' when Mode/=0 and Pair_Absolute='1' and Pair_Read='1' and Data_Long='1' and Pair_SP='0' and
        TState=3 and to_integer(unsigned(MCycle))=Pair_Address_Last+3 else '0';
    Upper_Port_Events(1)<=LEA_Commit and Data_Long;
    Upper_Port_Events(2)<=Arith_Commit;
    Upper_Port_Events(3)<=EX_SP_Result_WE;
    Upper_Port_Events(4)<='1' when Block_Long='1' and IncDec_16(2)='1' and Pair_Low_Wrap='1' and
        ((MCycle="001" and TState=3) or (MCycle/="001" and TState=2 and Wait_n='1')) else '0';
    Upper_Port_Events(5)<='1' when Wide_IncDec='1' and MCycle="001" and TState=3 and Exec_Control(EC_PAIR_SP)='0' and
        Pair_Low_Wrap='1' else '0';
    Upper_Port_Events(6)<='1' when Wide_Stack='1' and Exec_Control(EC_STACK_POP)='1' and MCycle="100" and TState=3 and Exec_Control(EC_PAIR_SP)='0' else '0';
    Upper_Port_Events(7)<='1' when Mode/=0 and TState=3 and IntCycle='0' and NMICycle='0' and Exec_Control(EC_IMM_PAIR)='1' and Exec_Control(EC_PAIR_SP)='0' and
        ((MCycle="011" and Stream_Long='0' and Data_Long='1') or (MCycle="100" and Stream_Long='1')) else '0';
    Upper_Port_WE<='1' when Upper_Port_Events/=x"00" else '0';
    Upper_Port_Index<=Upper_Mask(Pair_Commit_Index,Upper_Port_Events(0)) or Upper_Mask(EA_Target,Upper_Port_Events(1)) or
        Upper_Mask(Arith_Target,Upper_Port_Events(2)) or Upper_Mask(EX_SP_Index,Upper_Port_Events(3)) or
        Upper_Mask(RegAddrA,Upper_Port_Events(4)) or Upper_Mask(RegAddrA,Upper_Port_Events(5)) or
        Upper_Mask(Stack_Upper_Index,Upper_Port_Events(6)) or Upper_Mask(Load_Upper_Index,Upper_Port_Events(7));
    Upper_Inc_Byte<=std_logic_vector(unsigned(Reg24A(23 downto 16))-1) when IncDec_16(3)='1'
        else std_logic_vector(unsigned(Reg24A(23 downto 16))+1);
    Upper_Immediate_Byte<=DI_Reg when Stream_Long='1' and Data_Long='1' else x"00";
    Upper_Port_Data<=Upper_Mask(DI_Reg,Upper_Port_Events(0)) or Upper_Mask(EA_Result(23 downto 16),Upper_Port_Events(1)) or
        Upper_Mask(std_logic_vector(Arith_Result(23 downto 16)),Upper_Port_Events(2)) or Upper_Mask(EX_SP_Read(23 downto 16),Upper_Port_Events(3)) or
        Upper_Mask(Upper_Inc_Byte,Upper_Port_Events(4)) or Upper_Mask(Upper_Inc_Byte,Upper_Port_Events(5)) or
        Upper_Mask(DI_Reg,Upper_Port_Events(6)) or Upper_Mask(Upper_Immediate_Byte,Upper_Port_Events(7));


    process (RESET_n, CLK_n)
        variable Dec_Op : std_logic_vector(7 downto 0);
        variable IR_Load_Byte : std_logic_vector(7 downto 0);
        variable Dec_Page, Dec_XY : std_logic_vector(1 downto 0);
        variable Dec_Data, Dec_Stream, Dec_Has : std_logic;
        variable Load_Start_Cycle : natural range 2 to 5;
    begin
        if RESET_n = '0' then
            Load_Target<=(others=>'0');Load_SP<='0';Load_First<=(others=>'0');Load_Last<=(others=>'0');
            MADL<='0';Frame_Is_Call<='0';Frame_SPS<='0';Frame_State<=frame_idle;Frame_TS<=to_unsigned(1,3);Frame_Count<=0;
            Frame_Mode_Bit<='0';Frame_IM2<='0';Frame_RetN<='0';
            Mul_Left<=(others=>'0');Mul_Right<=(others=>'0');Mul_Product<=(others=>'0');
            EA_Result<=(others=>'0');
            I_Upper<=(others=>'0');IRQ_Vector<=(others=>'0');
            Ctrl_Target<=(others=>'0');Ctrl_Return<=(others=>'0');
            ADL_Mode<='0';
            Instruction_Has_Width<='0';
            Arith_Left<=(others=>'0');Arith_Right<=(others=>'0');Arith_Flags<=(others=>'0');
            Arith_Sub_Latched<='0';Arith_Carry_Latched<='0';Arith_Is_ADD<='0';
            EX_SP_Read<=(others=>'0');EX_SP_Source<=(others=>'0');EX_SP_Address<=(others=>'0');
            SPL <= (others=>'1');
            Extensions_Enabled<='0'; Unlock_Armed<='0';
            Width_Pending<='0'; Width_Code<=x"40"; Data_Long<='0'; Stream_Long<='0';
            Address_Bank_Reg<=x"00"; Index_Bank<=x"00";MBASE<=x"00";
            PC <= (others => '0');  -- Program Counter
            Address_Reg <= (others => '0');
			update_addr <= '0';
            TmpAddr <= (others => '0');
            IR <= x"00";Base_Group<=Decode_Base_Group(x"00");CB_Group<=Decode_CB_Group(x"00");ED_Group<=Decode_ED_Group(x"00"); Exec_Control<=(others=>'0'); Write_Class<=Classify_Write(x"00");
            ISet <= "00";
            XY_State <= "00";
            IStatus <= "00";
            MCycles <= "000";
            Data_Out_Reg <= "00000000";

            ACC <= (others => '1');
            F <= (others => '1');
            Ap <= (others => '1');
            Fp <= (others => '1');
            I <= (others => '0');
            R <= (others => '0');
            SP <= (others => '1');
            Alternate <= '0';

            Read_To_Reg_r <= "00000";
            F <= (others => '1');
            Arith16_r <= '0';
            BTR_r <= '0';
            Z16_r <= '0';
            ALU_Op_r <= "0000";
            ALU_cpi_r <= '0';
            Save_ALU_r <= '0';
            PreserveC_r <= '0';
            XY_Ind <= '0';

        elsif CLK_n'event and CLK_n = '1' then

            if CEN='1' and Frame_Start='1' then
                -- Finish the fetch/refresh phase before starting a memory T1.
                Frame_TS<=to_unsigned(4,3);Frame_Count<=0;Frame_RetN<='0';Frame_IM2<='0';Frame_Is_Call<='0';Frame_SPS<='0';
                if IRQ_IM0='1' then
                    -- Only CD and the eight RST encodings survive IACK decode.
                    -- Operand reads use the interrupted stream, never extra IACKs.
                    Frame_Mode_Bit<=ADL_Mode;Ctrl_Return<=std_logic_vector(PC);
                    if IR=x"CD" then
                        Frame_State<=frame_vector;Frame_Is_Call<='1';Ctrl_Target<=(others=>'0');
                        Address_Reg<=std_logic_vector(PC(15 downto 0));Address_Bank_Reg<=MBASE;
                        if ADL_Mode='1' then Address_Bank_Reg<=std_logic_vector(PC(23 downto 16));end if;
                    elsif Write_Class(3 downto 0)=x"E" then
                        Frame_State<=frame_push;Ctrl_Target<=x"0000" & "00" & IR(5 downto 3) & "000";
                        SPL<=Frame_Stack_Next;Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                        if ADL_Mode='1' then Frame_Count<=3;Data_Out_Reg<=std_logic_vector(PC(23 downto 16));
                        else Frame_Count<=2;Data_Out_Reg<=std_logic_vector(PC(15 downto 8));end if;
                    else
                        -- Reuse frame_mode as a bus-idle NOP completion, not a
                        -- mode-byte read. No new FSM encoding or data register.
                        Frame_State<=frame_mode;
                    end if;
                elsif Frame_Unsupported='1' then Frame_State<=frame_fault;Frame_TS<=to_unsigned(3,3);
                elsif Frame_Rst_Ready='1' then
                    Frame_State<=frame_push;Frame_Is_Call<='1';Frame_Mode_Bit<=ADL_Mode;Ctrl_Return<=std_logic_vector(PC);
                    Ctrl_Target<=x"0000" & "00" & IR(5 downto 3) & "000";
                    if Frame_Destination_Long='0' then
                        Frame_SPS<='1';Frame_Count<=2;SP<=Frame_Stack_Next(15 downto 0);
                        Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=MBASE;
                        Data_Out_Reg<=std_logic_vector(PC(15 downto 8));
                    else
                        SPL<=Frame_Stack_Next;Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                        if ADL_Mode='1' then Frame_Count<=3;Data_Out_Reg<=std_logic_vector(PC(23 downto 16));
                        else Frame_Count<=2;Data_Out_Reg<=std_logic_vector(PC(15 downto 8));end if;
                    end if;
                elsif Frame_Calling='1' then
                    -- Reuse the three-byte vector reader for CALL immediates.
                    Frame_State<=frame_vector;Frame_Is_Call<='1';Frame_Mode_Bit<=ADL_Mode;Ctrl_Target<=(others=>'0');
                    Address_Reg<=std_logic_vector(PC(15 downto 0));
                    Address_Bank_Reg<=MBASE;if ADL_Mode='1' then Address_Bank_Reg<=std_logic_vector(PC(23 downto 16));end if;
                elsif Frame_Entry='1' then
                    Frame_State<=frame_push;Frame_Mode_Bit<=ADL_Mode;Ctrl_Return<=std_logic_vector(PC);
                    if ADL_Mode='1' then Frame_Count<=3;else Frame_Count<=2;end if;
                    SPL<=Frame_Stack_Next;
                    Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                    if ADL_Mode='1' then Data_Out_Reg<=std_logic_vector(PC(23 downto 16));
                    else Data_Out_Reg<=std_logic_vector(PC(15 downto 8));end if;
                    if NMICycle='1' then Ctrl_Target<=x"000066";else Ctrl_Target<=x"000038";end if;
                    IRQ_Vector<=unsigned(I_Upper) & unsigned(I) & unsigned(DI_Reg);
                    if IntCycle='1' and IStatus="10" then Frame_IM2<='1';end if;
                else
                    Frame_State<=frame_mode;Ctrl_Target<=(others=>'0');
                    if ISet="10" then Frame_RetN<=not IR(3);end if;
                    Address_Reg<=std_logic_vector(SPL(15 downto 0));Address_Bank_Reg<=std_logic_vector(SPL(23 downto 16));
                end if;
            elsif CEN='1' and Frame_Active='1' then
                if Frame_End='1' then
                    -- The engine completes the instruction outside the normal T_Res path.
                    -- Discard its decoder state before fetching the return/entry target.
                    IR<=x"00";Base_Group<=Decode_Base_Group(x"00");CB_Group<=Decode_CB_Group(x"00");ED_Group<=Decode_ED_Group(x"00");ISet<="00";Exec_Control<=Decode_Execution(x"00", "00", "00", Extensions_Enabled, ADL_Mode, Data_Long, Stream_Long, '0', Mode);Write_Class<=Classify_Write(x"00");
                    Width_Pending<='0';Instruction_Has_Width<='0';
                    XY_State<="00";XY_Ind<='0';
                    Read_To_Reg_r<="00000";Save_ALU_r<='0';ALU_Op_r<="0000";
                end if;
                if Frame_State/=frame_fault then
                    if Frame_TS=4 then Frame_TS<=to_unsigned(1,3);
                    elsif Frame_TS=1 then Frame_TS<=to_unsigned(2,3);
                    elsif Frame_TS=2 then
                        if Wait_n='1' then Frame_TS<=to_unsigned(3,3);end if;
                    elsif Frame_TS=3 then
                        Frame_TS<=to_unsigned(1,3);
                        case Frame_State is
                        when frame_push =>
                            if Frame_SPS='1' then
                                if Frame_Count=2 then
                                    Frame_Count<=1;SP<=Frame_Stack_Next(15 downto 0);Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=MBASE;
                                    Data_Out_Reg<=Ctrl_Return(7 downto 0);
                                else
                                    Frame_SPS<='0';SPL<=Frame_Stack_Next;
                                    Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                                    if Frame_Mode_Bit='1' then Frame_Count<=1;Data_Out_Reg<=Ctrl_Return(23 downto 16);
                                    else Frame_Count<=0;Data_Out_Reg<=x"02";end if;
                                end if;
                            elsif Frame_Count>0 and not (IRQ_IM0='1' and MADL='0' and Frame_Count=1) then
                                Frame_Count<=Frame_Count-1;SPL<=Frame_Stack_Next;
                                Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                                if Frame_Count=3 then Data_Out_Reg<=Ctrl_Return(15 downto 8);
                                elsif Frame_Count=2 then Data_Out_Reg<=Ctrl_Return(7 downto 0);
                                else Data_Out_Reg<="0000001" & Frame_Mode_Bit;end if;
                            elsif Frame_IM2='1' then
                                Frame_State<=frame_vector;Frame_Count<=0;
                                Address_Reg<=std_logic_vector(IRQ_Vector(15 downto 0));Address_Bank_Reg<=std_logic_vector(IRQ_Vector(23 downto 16));
                            else
                                PC<=unsigned(Ctrl_Target);Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=Ctrl_Target(23 downto 16);
                                ADL_Mode<='1';Frame_State<=frame_idle;
                                if Frame_Is_Call='1' then
                                    ADL_Mode<=Frame_Destination_Long;
                                    if Frame_Destination_Long='0' then PC(23 downto 16)<=(others=>'0');Address_Bank_Reg<=MBASE;end if;
                                end if;
                            end if;
                        when frame_vector =>
                            if Frame_Is_Call='1' then
                                PC<=PC_Width(PC_Increment,ADL_Mode);
                                if Frame_Count=0 then Ctrl_Target(7 downto 0)<=DI_Reg;
                                elsif Frame_Count=1 then Ctrl_Target(15 downto 8)<=DI_Reg;
                                else Ctrl_Target(23 downto 16)<=DI_Reg;end if;
                                if Frame_Target_Last='0' then
                                    Frame_Count<=Frame_Count+1;
                                    Address_Reg<=std_logic_vector(resize(PC_Increment,16));Address_Bank_Reg<=MBASE;
                                    if ADL_Mode='1' then Address_Bank_Reg<=std_logic_vector(resize(shift_right(PC_Increment,16),8));end if;
                                elsif Frame_Take='0' then
                                    Frame_State<=frame_idle;
                                    Address_Reg<=std_logic_vector(resize(PC_Increment,16));Address_Bank_Reg<=MBASE;
                                    if ADL_Mode='1' then Address_Bank_Reg<=std_logic_vector(resize(shift_right(PC_Increment,16),8));end if;
                                else
                                    Ctrl_Return<=std_logic_vector(PC_Width(PC_Increment,ADL_Mode));Frame_State<=frame_push;
                                    if Frame_Destination_Long='0' then
                                        Frame_SPS<='1';Frame_Count<=2;SP<=Frame_Stack_Next(15 downto 0);
                                        Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=MBASE;
                                        Data_Out_Reg<=std_logic_vector(resize(shift_right(PC_Increment,8),8));
                                    else
                                        SPL<=Frame_Stack_Next;Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                                        if Frame_Mode_Bit='1' then Frame_Count<=3;Data_Out_Reg<=std_logic_vector(resize(shift_right(PC_Increment,16),8));
                                        else Frame_Count<=2;Data_Out_Reg<=std_logic_vector(resize(shift_right(PC_Increment,8),8));end if;
                                    end if;
                                end if;
                            else
                            if Frame_Count=0 then Ctrl_Target(7 downto 0)<=DI_Reg;
                            elsif Frame_Count=1 then Ctrl_Target(15 downto 8)<=DI_Reg;
                            else
                                PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=DI_Reg;
                                ADL_Mode<='1';Frame_State<=frame_idle;
                            end if;
                            if Frame_Count<2 then
                                Frame_Count<=Frame_Count+1;IRQ_Vector<=IRQ_Vector+1;
                                Address_Reg<=std_logic_vector(resize(IRQ_Vector+1,16));Address_Bank_Reg<=std_logic_vector(resize(shift_right(IRQ_Vector+1,16),8));
                            end if;
                            end if;
                        when frame_mode =>
                            if IRQ_IM0='1' then
                                Frame_State<=frame_idle;Address_Reg<=std_logic_vector(PC(15 downto 0));Address_Bank_Reg<=MBASE;
                                if ADL_Mode='1' then Address_Bank_Reg<=std_logic_vector(PC(23 downto 16));end if;
                            else
                                -- R36: only the saved bit 0 selects the restored ADL mode.
                                Frame_Mode_Bit<=DI_Reg(0);SPL<=Frame_Stack_Next;Frame_Count<=0;
                                if Stream_Long='1' or DI_Reg(0)='1' then
                                    Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                                else Address_Reg<=std_logic_vector(SP);Address_Bank_Reg<=MBASE;end if;
                                if Stream_Long='1' then Frame_State<=frame_long;
                                elsif DI_Reg(0)='1' then Frame_State<=frame_upper;
                                else Frame_State<=frame_short;end if;
                            end if;
                        when frame_upper =>
                            Ctrl_Target(23 downto 16)<=DI_Reg;SPL<=Frame_Stack_Next;Frame_State<=frame_short;Frame_Count<=0;
                            Address_Reg<=std_logic_vector(SP);Address_Bank_Reg<=MBASE;
                        when frame_long =>
                            SPL<=Frame_Stack_Next;
                            Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=Frame_Stack_Bank;
                            if Frame_Count=0 then Ctrl_Target(7 downto 0)<=DI_Reg;Frame_Count<=1;
                            elsif Frame_Count=1 then
                                Ctrl_Target(15 downto 8)<=DI_Reg;
                                if Frame_Mode_Bit='1' then Frame_Count<=2;
                                else
                                    PC<=to_unsigned(0,8) & unsigned(DI_Reg) & unsigned(Ctrl_Target(7 downto 0));
                                    Address_Reg<=DI_Reg & Ctrl_Target(7 downto 0);Address_Bank_Reg<=MBASE;ADL_Mode<='0';Frame_State<=frame_idle;
                                end if;
                            else
                                PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=DI_Reg;
                                ADL_Mode<='1';Frame_State<=frame_idle;
                            end if;
                        when frame_short =>
                            SP<=Frame_Stack_Next(15 downto 0);
                            Address_Reg<=std_logic_vector(Frame_Stack_Next(15 downto 0));Address_Bank_Reg<=MBASE;
                            if Frame_Count=0 then Ctrl_Target(7 downto 0)<=DI_Reg;Frame_Count<=1;
                            else
                                PC<=unsigned(Ctrl_Target(23 downto 16)) & unsigned(DI_Reg) & unsigned(Ctrl_Target(7 downto 0));
                                Address_Bank_Reg<=Ctrl_Target(23 downto 16);
                                if Frame_Mode_Bit='0' then PC(23 downto 16)<=(others=>'0');Address_Bank_Reg<=MBASE;end if;
                                Address_Reg<=DI_Reg & Ctrl_Target(7 downto 0);ADL_Mode<=Frame_Mode_Bit;Frame_State<=frame_idle;
                            end if;
                        when others=>null;
                        end case;
                    end if;
                end if;
            elsif ClkEn = '1' then

			update_addr <= '0';
            ALU_Op_r <= "0000";
            ALU_cpi_r <= '0';
            Save_ALU_r <= '0';
            Read_To_Reg_r <= "00000";

            MCycles <= MCycles_d;
            if MCycle="001" and TState=2 and Wait_n='1' then Address_Bank_Reg<=x"00";
            elsif T_Res='1' then
                -- R12: short data and Z80 instruction addresses use MBASE.
                Address_Bank_Reg<=x"00";
                if Extensions_Enabled='1' then Address_Bank_Reg<=MBASE;end if;
                -- Instruction stream stays PC24 even for Address_Reg short data-width prefix.
                if ADL_Mode='1' and (Set_Addr_To=aNone or (Set_Addr_To=aXY and NextIs_XY_Fetch='1')) then
                    Address_Bank_Reg<=std_logic_vector(PC(23 downto 16));
                end if;
                if Exec_Control(EC_DATA_LONG)='1' and IntCycle='0' and NMICycle='0' and (IORQ_i='0' or (Block_IO2='1' and IR(5)='0' and MCycle="010")) then
                    if EX_SP_Long='1' and Set_Addr_To=aSP then Address_Bank_Reg<=std_logic_vector(EX_SP_Address(23 downto 16));
                    elsif (Pair_Absolute='1' or Byte_Absolute='1') and Set_Addr_To=aZI then
                        if Inc_WZ='1' then
                            Address_Bank_Reg<=Address_Bank_Reg;
                            if Data_Long='1' and Address_Reg=x"FFFF" then Address_Bank_Reg<=std_logic_vector(unsigned(Address_Bank_Reg)+1);end if;
                        elsif Data_Long='1' and Stream_Long='1' then Address_Bank_Reg<=DI_Reg;
                        else Address_Bank_Reg<=x"00";end if;
                    elsif Set_Addr_To=aSP and (Wide_Stack='1' or PEA_Long='1' or Ctrl_Stack='1') then
                        Address_Bank_Reg<=std_logic_vector(SPL(23 downto 16));
                    elsif Set_Addr_To=aBC or Set_Addr_To=aDE then
                        Address_Bank_Reg<=Reg24C(23 downto 16);
                    elsif Set_Addr_To=aXY then
                        if XY_State="00" then Address_Bank_Reg<=Reg24C(23 downto 16);
                        elsif NextIs_XY_Fetch='0' then Address_Bank_Reg<=Index_Bank;end if;
                    end if;
                end if;
            end if;
            -- Explicit local gate, not Address_Reg Zilog architectural register.
            if T_Res='1' and IORQ_i='1' and Write_Decode='1' then
                if DATA_EXTENDED and Address_Reg=x"E7E7" then
                    if Data_Out_Reg=x"00" then
                        if ADL_Mode='0' then
                            Extensions_Enabled<='0';MBASE<=x"00";MADL<='0';
                            -- The next Z80 fetch must use the cleared MBASE too.
                            Address_Bank_Reg<=x"00";
                        end if;Unlock_Armed<='0';
                    elsif Data_Out_Reg=x"A5" then Unlock_Armed<='1';
                    elsif Data_Out_Reg=x"5A" and Unlock_Armed='1' then Extensions_Enabled<='1';Unlock_Armed<='0';
                    else Unlock_Armed<='0';end if;
                else Unlock_Armed<='0';end if;
            end if;

            if IMode /= "11" then
                IStatus <= IMode;
            end if;

            Arith16_r <= Arith16;
            PreserveC_r <= PreserveC;
            if ISet = "10" and ALU_OP(2) = '0' and ALU_OP(0) = '1' and MCycle = "011" then
                Z16_r <= '1';
            else
                Z16_r <= '0';
            end if;

            if MCycle  = "001" and TState(2) = '0' then
            -- MCycle = 1 and TState = 1, 2, or 3

                if TState = 2 and Wait_n = '1' then
                    if Mode < 2 then
						update_addr <= '1';
                        Address_Reg(7 downto 0) <= std_logic_vector(R);
                        Address_Reg(15 downto 8) <= I;
                        R(6 downto 0) <= R(6 downto 0) + 1;
                    end if;

                    if Jump = '0' and Call = '0' and NMICycle = '0' and IntCycle = '0' and not (Halt_FF = '1' or Halt = '1') then
                        PC <= PC_Width(PC_Increment,ADL_Mode);
                    end if;

                    Dec_Op:=DInst;Dec_Page:="00";Dec_XY:=XY_State;
                    Dec_Data:=Data_Long;Dec_Stream:=Stream_Long;Dec_Has:=Instruction_Has_Width;
                    if Extensions_Enabled='1' and IntCycle='0' and NMICycle='0' and Halt_FF='0' then
                        if Prefix/="10" and Prefix/="01" and (DInst=x"40" or DInst=x"49" or DInst=x"52" or DInst=x"5B") then
                            Width_Pending<='1'; Width_Code<=DInst;
                            Dec_Data:='0';Dec_Stream:='0';Dec_Has:='0';
                        -- R19.1: DD/FD CB reads its final opcode in M7, not M1.
                        -- Consume the width at the indexed CB fetch so M6 address
                        -- calculation already uses it; never carry it to the next instruction.
                        elsif Prefix="10" or Prefix="01" or (DInst/=x"DD" and DInst/=x"FD" and DInst/=x"ED" and DInst/=x"CB") or
                            (DInst=x"CB" and Prefix="11" and (IR=x"DD" or IR=x"FD")) then
                            Dec_Has:=Width_Pending;
                            if Width_Pending='1' then Dec_Data:=Width_Code(3);Dec_Stream:=Width_Code(4);
                            else Dec_Data:=ADL_Mode;Dec_Stream:=ADL_Mode;end if;
                            Width_Pending<='0';
                        end if;
                    else Width_Pending<='0';Dec_Data:='0';Dec_Stream:='0';Dec_Has:='0';end if;
                    if IntCycle = '1' and IStatus = "01" then
                        Dec_Op:=x"FF";
                    elsif (Halt_FF = '1' and IRQ_IM0='0') or (IntCycle = '1' and IStatus = "10") or NMICycle = '1' or
                        (IRQ_IM0='1' and DInst/=x"CD" and not (DInst(7 downto 6)="11" and DInst(2 downto 0)="111")) then
                        Dec_Op:=x"00";
                    else
                        Dec_Op:=DInst;
                    end if;

                    Dec_Page:="00";
                    if Prefix /= "00" then
                        if Prefix = "11" then
                            if Extensions_Enabled='1' and (IR=x"40" or IR=x"49" or IR=x"52" or IR=x"5B") then null;
                            elsif IR(5) = '1' then
                                Dec_XY:="10";
                            else
                                Dec_XY:="01";
                            end if;
                        else
                            if Prefix = "10" then
                                Dec_XY:="00";
                                XY_Ind <= '0';
                            end if;
                            Dec_Page:=Prefix;
                        end if;
                    else
                        Dec_XY:="00";
                        XY_Ind <= '0';
                    end if;
                    IR<=Dec_Op;Base_Group<=Decode_Base_Group(Dec_Op);CB_Group<=Decode_CB_Group(Dec_Op);ED_Group<=Decode_ED_Group(Dec_Op);ISet<=Dec_Page;XY_State<=Dec_XY;
                    Data_Long<=Dec_Data;Stream_Long<=Dec_Stream;Instruction_Has_Width<=Dec_Has;
                    Write_Class<=Classify_Write(Dec_Op);
                    Exec_Control<=Decode_Execution(Dec_Op, Dec_Page, Dec_XY, Extensions_Enabled, ADL_Mode,
                                                   Dec_Data, Dec_Stream, Dec_Has, Mode);
                end if;

            else
            -- either (MCycle > 1) OR (MCycle = 1 AND TState > 3)

                if MCycle = "110" and SP_Readback='0' and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0' and Block_IO2='0' then
                    XY_Ind <= '1';
                    if Prefix = "01" then
                        ISet <= "01";
                    end if;
                end if;

                if T_Res = '1' then
					update_addr <= '1';
                    BTR_r <= (I_BT or I_BC or I_BTR) and not No_BTR;
                    if Jump = '1' then
                        Address_Reg(15 downto 8) <= DI_Reg;
                        Address_Reg(7 downto 0) <= TmpAddr(7 downto 0);
                        PC(15 downto 8) <= unsigned(DI_Reg);
                        PC(7 downto 0) <= unsigned(TmpAddr(7 downto 0));
                    elsif JumpXY = '1' then
                        Address_Reg <= RegBusC;
                        if Exec_Control(EC_JP_INDIRECT)='1' then
                            if Data_Long='1' then
                                PC<=unsigned(Reg24C);
                                Address_Bank_Reg<=Reg24C(23 downto 16);ADL_Mode<='1';
                            else PC<=resize(unsigned(RegBusC),24);Address_Bank_Reg<=MBASE;ADL_Mode<='0';end if;
                        else PC <= resize(unsigned(RegBusC),24);end if;
                    elsif Call = '1' or RstP = '1' then
                        Address_Reg <= TmpAddr;
                        PC <= resize(unsigned(TmpAddr),24);
                    elsif MCycle = MCycles and NMICycle = '1' and IRQ_Long='0' then
                        Address_Reg <= "0000000001100110";
                        PC <= to_unsigned(16#66#,24);
                    elsif MCycle = "011" and IntCycle = '1' and IStatus = "10" and IRQ_Long='0' then
                        Address_Reg(15 downto 8) <= I;
                        Address_Reg(7 downto 0) <= TmpAddr(7 downto 0);
                        PC(15 downto 8) <= unsigned(I);
                        PC(7 downto 0) <= unsigned(TmpAddr(7 downto 0));
                    else
                        case Set_Addr_To is
                        when aXY =>
                            if XY_State = "00" then
                                Address_Reg <= RegBusC;
                            else
                                if NextIs_XY_Fetch = '1' then
                                    Address_Reg <= std_logic_vector(PC(15 downto 0));
                                else
                                    Address_Reg <= TmpAddr;
                                end if;
                            end if;
                        when aIOA =>
                            if Mode = 3 then
                                -- Memory map I/O on GBZ80
                                Address_Reg(15 downto 8) <= (others => '1');
                            elsif Mode = 2 then
                                -- Duplicate I/O address on 8080
                                Address_Reg(15 downto 8) <= DI_Reg;
                            else
                                Address_Reg(15 downto 8) <= ACC;
                            end if;
                            Address_Reg(7 downto 0) <= DI_Reg;
                        when aSP =>
                            if EX_SP_Long='1' then Address_Reg<=std_logic_vector(EX_SP_Address(15 downto 0));elsif Wide_Stack='1' or PEA_Long='1' or Ctrl_Stack='1' then Address_Reg<=std_logic_vector(SPL(15 downto 0));else Address_Reg <= std_logic_vector(SP);end if;
                        when aBC =>
                            if Exec_Control(EC_TSTIO)='1' then
                                -- Only TSTIO forces port bits 15:8 to zero; ordinary IN/OUT retain BC16.
                                Address_Reg <= x"00" & RegBusC(7 downto 0);
                            elsif Mode = 3 and IORQ_i = '1' then
                                -- Memory map I/O on GBZ80
                                Address_Reg(15 downto 8) <= (others => '1');
                                Address_Reg(7 downto 0) <= RegBusC(7 downto 0);
                            else
                                Address_Reg <= RegBusC;
                            end if;
                        when aDE =>
                            Address_Reg <= RegBusC;
                        when aZI =>
                            if Inc_WZ = '1' then
                                if Pair_Absolute='1' then Address_Reg<=std_logic_vector(unsigned(Address_Reg)+1);elsif SP_Readback='1' and MCycle="101" then Address_Reg<=std_logic_vector(unsigned(Address_Reg)+1);else Address_Reg <= std_logic_vector(unsigned(TmpAddr) + 1);end if;
                            elsif (Pair_Absolute='1' or Byte_Absolute='1') and Stream_Long='1' then Address_Reg<=TmpAddr;
                            else
                                Address_Reg(15 downto 8) <= DI_Reg;
                                Address_Reg(7 downto 0) <= TmpAddr(7 downto 0);
                            end if;
                        when others =>
                            Address_Reg <= std_logic_vector(PC(15 downto 0));
                        end case;
                    end if;

                    Save_ALU_r <= Save_ALU;
                    ALU_cpi_r <= ALU_cpi;
                    ALU_Op_r <= ALU_Op;

                    if I_CPL = '1' then
                        -- CPL
                        ACC <= not ACC;
                        F(Flag_Y) <= not ACC(5);
                        F(Flag_H) <= '1';
                        F(Flag_X) <= not ACC(3);
                        F(Flag_N) <= '1';
                    end if;
                    if I_CCF = '1' then
                        -- CCF
                        F(Flag_C) <= not F(Flag_C);
                        F(Flag_Y) <= ACC(5);
                        F(Flag_H) <= F(Flag_C);
                        F(Flag_X) <= ACC(3);
                        F(Flag_N) <= '0';
                    end if;
                    if I_SCF = '1' then
                        -- SCF
                        F(Flag_C) <= '1';
                        F(Flag_Y) <= ACC(5);
                        F(Flag_H) <= '0';
                        F(Flag_X) <= ACC(3);
                        F(Flag_N) <= '0';
                    end if;
                end if;

                if TState = 2 and Wait_n = '1' then
                    if ISet = "01" and MCycle = "111" then
                        IR <= DInst;Base_Group<=Decode_Base_Group(DInst);CB_Group<=Decode_CB_Group(DInst);ED_Group<=Decode_ED_Group(DInst);Write_Class<=Classify_Write(DInst);
                        Exec_Control<=Decode_Execution(DInst, ISet, XY_State, Extensions_Enabled, ADL_Mode,
                                                       Data_Long, Stream_Long, Instruction_Has_Width, Mode);
                    end if;
                    if JumpE = '1' then
                        PC <= PC_Width(unsigned(signed(PC) + signed(DI_Reg)),ADL_Mode);
                    elsif Inc_PC = '1' then
                        PC <= PC_Width(PC_Increment,ADL_Mode);
                    end if;
                    if BTR_r = '1' then
                        -- Refetch the width prefix as well as ED and the block opcode.
                        -- This also gives an interrupt Address_Reg restart PC including the suffix.
                        if Block_Instruction='1' and Instruction_Has_Width='1' then PC<=PC_Width(PC-3,ADL_Mode);
                        else PC <= PC_Width(PC-2,ADL_Mode);end if;
                    end if;
                    if RstP = '1' then
                        TmpAddr <= (others =>'0');
                        TmpAddr(5 downto 3) <= IR(5 downto 3);
                    end if;
                end if;
                if TState = 3 and MCycle = "110" and SP_Readback='0' and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0' and Block_IO2='0' then
                    TmpAddr <= std_logic_vector(signed(RegBusC) + signed(DI_Reg));
                    if Data_Long='1' then
                        TmpAddr<=std_logic_vector(Indexed_Address(15 downto 0));
                        Index_Bank<=std_logic_vector(Indexed_Address(23 downto 16));
                    end if;
                end if;

                if (TState = 2 and Wait_n = '1') or (TState = 4 and MCycle = "001") then
                    if IncDec_16(2 downto 0) = "111" then
                        if Wide_Stack='1' or Wide_IncDec='1' or PEA_Long='1' or Ctrl_Stack='1' then
                            if IncDec_16(3)='1' then SPL<=SPL-1;else SPL<=SPL+1;end if;
                        elsif IncDec_16(3) = '1' then
                            SP <= SP - 1;
                        else
                            SP <= SP + 1;
                        end if;
                    end if;
                end if;

                if LDSPHL = '1' then
                    if Exec_Control(EC_DATA_LONG)='1' then SPL<=unsigned(Reg24C);
                    else SP <= unsigned(RegBusC);end if;
                end if;
                if ExchangeAF = '1' then
                    Ap <= ACC;
                    ACC <= Ap;
                    Fp <= F;
                    F <= Fp;
                end if;
                if ExchangeRS = '1' then
                    Alternate <= not Alternate;
                end if;
            end if;

            if Exec_Control(EC_DATA_LONG)='1' and ExchangeDH='1' and TState=3 then
                null;
                null;
            end if;
            if Mode/=0 and Pair_Absolute='1' and Pair_Read='1' and Data_Long='1' and TState=3 and to_integer(unsigned(MCycle))=Pair_Address_Last+3 then
                if Pair_SP='1' then SPL(23 downto 16)<=unsigned(DI_Reg);
                else null;end if;
            end if;
            -- Capture source before computing: no combinational CPU bus reaches DSP output.
            if Ctrl_Call='1' and TState=3 then
                case MCycle is
                when "010"=>Ctrl_Target(7 downto 0)<=DI_Reg;
                when "011"=>Ctrl_Target(15 downto 8)<=DI_Reg;
                when "100"=>Ctrl_Target(23 downto 16)<=DI_Reg;Ctrl_Return<=std_logic_vector(PC);
                when others=>null;
                end case;
            end if;
            if Ctrl_Rst='1' and IRQ_Long='0' and MCycle="001" and TState=4 then
                Ctrl_Return<=std_logic_vector(PC);Ctrl_Target<=x"0000" & "00" & IR(5 downto 3) & "000";
            end if;
            if Ctrl_Ret='1' and TState=3 then
                if MCycle="010" then Ctrl_Target(7 downto 0)<=DI_Reg;
                elsif MCycle="011" then Ctrl_Target(15 downto 8)<=DI_Reg;end if;
            end if;
            if Ctrl_Taken='1' and TState=3 and
                ((Ctrl_Call='1' and MCycle="111") or (Ctrl_Rst='1' and IRQ_IM2='0' and MCycle="100") or (Ctrl_Ret='1' and MCycle="100")) then
                if Ctrl_Ret='1' then
                    PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));
                    Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=DI_Reg;
                else PC<=unsigned(Ctrl_Target);Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=Ctrl_Target(23 downto 16);end if;
            end if;
            if IRQ_Long='1' then
                if MCycle="001" and TState=4 then
                    Ctrl_Return<=std_logic_vector(PC);
                    if NMICycle='1' then Ctrl_Target<=x"000066";else Ctrl_Target<=x"000038";end if;
                    IRQ_Vector<=unsigned(I_Upper) & unsigned(I) & unsigned(DI_Reg);
                end if;
                if T_Res='1' and unsigned(MCycle)<=3 then
                    Address_Reg<=std_logic_vector(SPL(15 downto 0));Address_Bank_Reg<=std_logic_vector(SPL(23 downto 16));
                end if;
                if IRQ_IM2='1' then
                    if TState=2 and Wait_n='1' and (MCycle="101" or MCycle="110") then IRQ_Vector<=IRQ_Vector+1;end if;
                    if T_Res='1' and (MCycle="100" or MCycle="101" or MCycle="110") then
                        Address_Reg<=std_logic_vector(IRQ_Vector(15 downto 0));Address_Bank_Reg<=std_logic_vector(IRQ_Vector(23 downto 16));
                    end if;
                    if TState=3 then
                        if MCycle="101" then Ctrl_Target(7 downto 0)<=DI_Reg;
                        elsif MCycle="110" then Ctrl_Target(15 downto 8)<=DI_Reg;
                        elsif MCycle="111" then
                            PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));
                            Address_Reg<=Ctrl_Target(15 downto 0);Address_Bank_Reg<=DI_Reg;
                        end if;
                    end if;
                end if;
            end if;
            if Exec_Control(EC_IV_WRITE)='1' and Exec_Normal='1' and MCycle="001" and TState=4 then
                I_Upper<=RegBusA(15 downto 8);I<=RegBusA(7 downto 0);
            end if;
            if JP_Commit='1' then
                if Stream_Long='1' then
                    PC<=(unsigned(DI_Reg) & unsigned(TmpAddr));Address_Reg<=TmpAddr;Address_Bank_Reg<=DI_Reg;ADL_Mode<='1';
                else
                    PC<=(to_unsigned(0,8) & unsigned(DI_Reg) & unsigned(TmpAddr(7 downto 0)));
                    Address_Reg<=DI_Reg & TmpAddr(7 downto 0);Address_Bank_Reg<=MBASE;ADL_Mode<='0';
                end if;
            end if;
            -- The displacement is stable after the external read's falling T3 edge.
            -- Share Indexed_Address, then hold all 24 bits through destination/stack writes.
            if EA_Active='1' and MCycle="010" and TState=3 then EA_Result<=std_logic_vector(Indexed_Address);end if;
            if LEA_Commit='1' and Data_Long='1' then null;end if;
            if Mul_Active='1' and MCycle="001" then
                if TState=4 then Mul_Left<=Mul_Operand(15 downto 8);Mul_Right<=Mul_Operand(7 downto 0);end if;
                if TState=5 then Mul_Product<=Mul_Left*Mul_Right;end if;
            end if;
            if Mul_Commit='1' and Exec_Control(EC_PAIR_SP)='1' then
                if Data_Long='1' then SPL(15 downto 0)<=Mul_Product;else SP<=Mul_Product;end if;
            end if;
            if Arith_Long='1' and MCycle="001" and TState=4 then
                Arith_Left<=unsigned(Reg24A);
                if Exec_Control(EC_PAIR_SP)='1' then Arith_Right<=SPL;
                else Arith_Right<=unsigned(Reg24B);end if;
                Arith_Flags<=F;Arith_Sub_Latched<=Arith_Sub;Arith_Carry_Latched<=Arith_Carry;
                Arith_Is_ADD<=Exec_Control(EC_PAGE_BASE);
            end if;
            if Arith_Commit='1' then
                null;
            end if;
            if Pair_Indirect='1' then
                if Pair_Indexed='0' and MCycle="001" and TState=3 then
                    EX_SP_Address(15 downto 0)<=unsigned(RegBusC);
                    if Data_Long='1' then EX_SP_Address(23 downto 16)<=unsigned(Reg24C(23 downto 16));
                    else EX_SP_Address(23 downto 16)<=unsigned(MBASE);end if;
                end if;
                if MCycle="001" and TState=4 then EX_SP_Source<=Reg24A;end if;
                if Pair_Indexed='1' and MCycle="010" and TState=3 then
                    EX_SP_Address(15 downto 0)<=unsigned(Indexed_Address(15 downto 0));
                    if Data_Long='1' then EX_SP_Address(23 downto 16)<=unsigned(Indexed_Address(23 downto 16));
                    else EX_SP_Address(23 downto 16)<=unsigned(MBASE);end if;
                end if;
                -- Work address changes only once, on an accepted data T2.
                if TState=2 and Wait_n='1' and (to_integer(unsigned(MCycle))=2+Indirect_Offset or to_integer(unsigned(MCycle))=3+Indirect_Offset) then
                    if Data_Long='0' then EX_SP_Address(15 downto 0)<=EX_SP_Address_Next(15 downto 0);end if;
                end if;
                -- Latch the complete request payload at the end of the preceding cycle.
                -- The final cycle restores PC fetch through the ordinary address logic.
                if T_Res='1' and (to_integer(unsigned(MCycle))=1+Indirect_Offset or to_integer(unsigned(MCycle))=2+Indirect_Offset or (to_integer(unsigned(MCycle))=3+Indirect_Offset and Data_Long='1')) then
                    Address_Reg<=std_logic_vector(EX_SP_Address(15 downto 0));
                    Address_Bank_Reg<=std_logic_vector(EX_SP_Address(23 downto 16));
                end if;
            end if;
            -- Shared incrementer for EX(SP) and indirect pair transfers.
            if TState=2 and Wait_n='1' and
               ((EX_SP_Long='1' and (MCycle="010" or MCycle="011" or MCycle="101" or MCycle="110")) or
                (Pair_Indirect='1' and Data_Long='1' and (to_integer(unsigned(MCycle))=2+Indirect_Offset or to_integer(unsigned(MCycle))=3+Indirect_Offset))) then
                EX_SP_Address<=EX_SP_Address_Next;
            end if;
            if EX_SP_Long='1' then
                if MCycle="001" and TState=3 then EX_SP_Address<=SPL;end if;
                if MCycle="001" and TState=4 then
                    EX_SP_Source<=Reg24A;
                end if;
                if TState=2 and Wait_n='1' then
                    case MCycle is
                    when "010"|"011"|"101"|"110"=>null; -- shared increment above
                    when "100"=>EX_SP_Address<=SPL;
                    when others=>null;
                    end case;
                end if;
            end if;
            if EX_SP_Long='1' and TState=3 then
                case MCycle is
                when "010"=>EX_SP_Read(7 downto 0)<=DI_Reg;
                when "011"=>EX_SP_Read(15 downto 8)<=DI_Reg;
                when "100"=>EX_SP_Read(23 downto 16)<=DI_Reg;
                when others=>null;
                end case;
            end if;
            if EX_SP_Result_WE='1' then null;end if;
            if Load_Active='1' and MCycle="001" and TState=3 then
                Load_SP<='0';EX_SP_Read<=(others=>'0');
                if Exec_Control(EC_LOAD_IMM)='1' then
                    Load_Target<=Load_Upper_Index;Load_Start_Cycle:=2;
                    if Exec_Control(EC_PAIR_SP)='1' then Load_SP<='1';end if;
                elsif Exec_Control(EC_LOAD_ABS)='1' then
                    Load_Target<=Pair_Upper_Index;Load_SP<=Pair_SP;
                    if Stream_Long='1' then Load_Start_Cycle:=5;else Load_Start_Cycle:=4;end if;
                else
                    Load_Target<=Indirect_Index;Load_Start_Cycle:=2+Indirect_Offset;
                end if;
                Load_First<=to_unsigned(Load_Start_Cycle,3);
                if Load_Three='1' then Load_Last<=to_unsigned(Load_Start_Cycle+2,3);
                else Load_Last<=to_unsigned(Load_Start_Cycle+1,3);end if;
            end if;
            if Load_Active='1' and TState=3 then
                if unsigned(MCycle)=Load_First then EX_SP_Read(7 downto 0)<=DI_Reg;
                elsif unsigned(MCycle)=Load_First+1 then EX_SP_Read(15 downto 8)<=DI_Reg;
                elsif unsigned(MCycle)=Load_Last then EX_SP_Read(23 downto 16)<=DI_Reg;end if;
            end if;
            if Load_Commit='1' and Load_SP='1' then
                if Data_Long='1' then SPL<=unsigned(Load_Result);
                else SP<=unsigned(Load_Result(15 downto 0));end if;
            end if;

            -- Use exactly the original lower16 register Write_Decode edge: once per byte,
            -- never while T2 is held by WAIT. BC decrements in M1/T3; HL/DE in data T2.
            if Block_Long='1' and IncDec_16(2)='1' and
               ((MCycle="001" and TState=3) or (MCycle/="001" and TState=2 and Wait_n='1')) then
                null;
            end if;
            if Wide_IncDec='1'   and MCycle="001" and TState=3 and Exec_Control(EC_PAIR_SP)='0' then
                if IncDec_16(3)='1' and RegBusA=x"0000" then
                    null;
                elsif IncDec_16(3)='0' and RegBusA=x"FFFF" then
                    null;
                end if;
            end if;
            if Wide_Stack='1' and Exec_Control(EC_STACK_POP)='1' and MCycle="100" and TState=3 and Exec_Control(EC_PAIR_SP)='0' then
                null;
            end if;
            if Mode/=0 and TState=3 and IntCycle='0'  and NMICycle='0' and Exec_Control(EC_IMM_PAIR)='1' and Pair_Indexed='0' then
                if MCycle="011" and Stream_Long='0' and Data_Long='1' then
                    if Exec_Control(EC_PAIR_SP)='1' then SPL(23 downto 16)<=(others=>'0');
                    else null;end if;
                elsif MCycle="100" and Stream_Long='1' then
                    if Exec_Control(EC_PAIR_SP)='1' then
                        if Data_Long='1' then SPL(23 downto 16)<=unsigned(DI_Reg);end if;
                    else
                        if Data_Long='1' then null;
                        else null;end if;
                    end if;
                end if;
            end if;
            if TState = 3 then
                if LDZ = '1' then
                    TmpAddr(7 downto 0) <= DI_Reg;
                end if;
                if LDW = '1' then
                    TmpAddr(15 downto 8) <= DI_Reg;
                end if;

                if Special_LD(2) = '1' then
                    case Special_LD(1 downto 0) is
                    when "00" | "01" =>
                        -- R37: LD A,I/R share one byte value for A and flag generation.
                        if Special_LD(0)='0' then IR_Load_Byte:=I;
                        else IR_Load_Byte:=std_logic_vector(R);end if;
                        ACC <= IR_Load_Byte;
                        F(Flag_S) <= IR_Load_Byte(7);
                        if IR_Load_Byte=x"00" then F(Flag_Z)<='1';else F(Flag_Z)<='0';end if;
                        F(Flag_H) <= '0';
                        F(Flag_P) <= IntE_FF2;
                        F(Flag_N) <= '0';
                        F(Flag_X) <= IR_Load_Byte(3);
                        F(Flag_Y) <= IR_Load_Byte(5);
                        -- Carry is preserved; LD I,A and LD R,A remain flag-neutral.
                    when "10" =>
                        I <= ACC;
                    when others =>
                        R <= unsigned(ACC);
                    end case;
                end if;
            end if;

            if Block_IO2='0' and ((I_DJNZ = '0' and Save_ALU_r = '1') or ALU_Op_r = "1001") then
                if Mode = 3 then
                    F(6) <= F_Out(6);
                    F(5) <= F_Out(5);
                    F(7) <= F_Out(7);
                    if PreserveC_r = '0' then
                        F(4) <= F_Out(4);
                    end if;
                else
                    F(7 downto 1) <= F_Out(7 downto 1);
                    if PreserveC_r = '0' then
                        F(Flag_C) <= F_Out(0);
                    end if;
                end if;
            end if;
            -- B/C arithmetic uses the existing byte ALU, preserving every other flag.
            if Block_IO2='1' then
                if MCycle="101" and Save_ALU_r='1' then F(Flag_Z)<=F_Out(Flag_Z);end if;
                if MCycle="011" and T_Res='1' then F(Flag_N)<=Data_Out_Reg(7);end if;
            end if;
            if T_Res = '1' and I_INRC = '1' then
                F(Flag_H) <= '0';
                F(Flag_N) <= '0';
                if DI_Reg(7 downto 0) = "00000000" then
                    F(Flag_Z) <= '1';
                else
                    F(Flag_Z) <= '0';
                end if;
                F(Flag_S) <= DI_Reg(7);
                F(Flag_P) <= not (DI_Reg(0) xor DI_Reg(1) xor DI_Reg(2) xor DI_Reg(3) xor
                    DI_Reg(4) xor DI_Reg(5) xor DI_Reg(6) xor DI_Reg(7));
            end if;

            if Arith_Commit='1' then
                F(Flag_H)<=Arith_Half;F(Flag_N)<=Arith_Sub_Latched;F(Flag_C)<=Arith_Carry_Out;
                F(Flag_X)<=Arith_Result(19);F(Flag_Y)<=Arith_Result(21);
                if Arith_Is_ADD='1' then
                    F(Flag_S)<=Arith_Flags(Flag_S);F(Flag_Z)<=Arith_Flags(Flag_Z);F(Flag_P)<=Arith_Flags(Flag_P);
                else
                    F(Flag_S)<=Arith_Result(23);F(Flag_P)<=Arith_Overflow;
                    if Arith_Result=0 then F(Flag_Z)<='1';else F(Flag_Z)<='0';end if;
                end if;
            end if;
            if TState = 1 and Auto_Wait_t1 = '0' then
                Data_Out_Reg <= BusB;
                if Pair_Indirect='1' and Indirect_Read='0' then
                    if to_integer(unsigned(MCycle))=2+Indirect_Offset then Data_Out_Reg<=EX_SP_Source(7 downto 0);
                    elsif to_integer(unsigned(MCycle))=3+Indirect_Offset then Data_Out_Reg<=EX_SP_Source(15 downto 8);
                    elsif to_integer(unsigned(MCycle))=4+Indirect_Offset then Data_Out_Reg<=EX_SP_Source(23 downto 16);end if;
                end if;
                if Wide_Stack='1' and Exec_Control(EC_STACK_PUSH)='1' and MCycle="010" then
                    if Exec_Control(EC_PAIR_SP)='1' then Data_Out_Reg<=x"00";
                    else Data_Out_Reg<=Reg24UpperU;end if;
                end if;
                if Ctrl_Call='1' then
                    if MCycle="101" then Data_Out_Reg<=Ctrl_Return(23 downto 16);
                    elsif MCycle="110" then Data_Out_Reg<=Ctrl_Return(15 downto 8);
                    elsif MCycle="111" then Data_Out_Reg<=Ctrl_Return(7 downto 0);end if;
                elsif Ctrl_Rst='1' then
                    if MCycle="010" then Data_Out_Reg<=Ctrl_Return(23 downto 16);
                    elsif MCycle="011" then Data_Out_Reg<=Ctrl_Return(15 downto 8);
                    elsif MCycle="100" then Data_Out_Reg<=Ctrl_Return(7 downto 0);end if;
                end if;
                if PEA_Active='1' then
                    if Data_Long='1' then
                        case MCycle is
                        when "011"=>Data_Out_Reg<=EA_Result(23 downto 16);
                        when "100"=>Data_Out_Reg<=EA_Result(15 downto 8);
                        when "101"=>Data_Out_Reg<=EA_Result(7 downto 0);
                        when others=>null;
                        end case;
                    else
                        if MCycle="011" then Data_Out_Reg<=EA_Result(15 downto 8);elsif MCycle="100" then Data_Out_Reg<=EA_Result(7 downto 0);end if;
                    end if;
                end if;
                if EX_SP_Long='1' then
                    case MCycle is
                    when "101"=>Data_Out_Reg<=EX_SP_Source(7 downto 0);
                    when "110"=>Data_Out_Reg<=EX_SP_Source(15 downto 8);
                    when "111"=>Data_Out_Reg<=EX_SP_Source(23 downto 16);
                    when others=>null;
                    end case;
                end if;
                if I_RLD = '1' then
                    Data_Out_Reg(3 downto 0) <= BusA(3 downto 0);
                    Data_Out_Reg(7 downto 4) <= BusB(3 downto 0);
                end if;
                if I_RRD = '1' then
                    Data_Out_Reg(3 downto 0) <= BusB(7 downto 4);
                    Data_Out_Reg(7 downto 4) <= BusA(3 downto 0);
                end if;
            end if;

            if T_Res = '1' then
                Read_To_Reg_r(3 downto 0) <= Set_BusA_To;
                Read_To_Reg_r(4) <= Read_To_Reg;
                if Read_To_Acc = '1' then
                    Read_To_Reg_r(3 downto 0) <= "0111";
                    Read_To_Reg_r(4) <= '1';
                end if;
            end if;

            if TState = 1 and I_BT = '1' then
                F(Flag_X) <= ALU_Q(3);
                F(Flag_Y) <= ALU_Q(1);
                F(Flag_H) <= '0';
                F(Flag_N) <= '0';
            end if;
            if I_BC = '1' or I_BT = '1' then
                F(Flag_P) <= IncDecZ;
            end if;

            if (TState = 1 and Save_ALU_r = '0' and Auto_Wait_t1 = '0') or
                (Save_ALU_r = '1' and ALU_OP_r /= "0111") then
                case Read_To_Reg_r is
                when "10111" =>
                    ACC <= Save_Mux;
                when "10110" =>
                    Data_Out_Reg <= Save_Mux;
                when "11000" =>
                    if Data_Long='1' and ((Exec_Control(EC_SP_IMMEDIATE)='1') or (Pair_Absolute='1' and Pair_Read='1' and Pair_SP='1')) then SPL(7 downto 0)<=unsigned(Save_Mux);
                    else SP(7 downto 0)<=unsigned(Save_Mux);end if;
                when "11001" =>
                    if Data_Long='1' and ((Exec_Control(EC_SP_IMMEDIATE)='1') or (Pair_Absolute='1' and Pair_Read='1' and Pair_SP='1')) then SPL(15 downto 8)<=unsigned(Save_Mux);
                    else SP(15 downto 8)<=unsigned(Save_Mux);end if;
                when "11011" =>
                    F <= Save_Mux;
                when others =>
                end case;
                if XYbit_undoc='1' then
                    Data_Out_Reg <= ALU_Q;
                end if;
            end if;

            if Exec_Control(EC_MADL_OPCODE)='1' and Exec_Normal='1' and MCycle="001" and TState=4 then
                MADL<=Exec_Control(EC_MADL_SET);
            end if;
            -- LD MB,A / LD A,MB are ADL-only; Z80 mode is a NOP.
            if Exec_Control(EC_MB_VALID)='1' and Exec_Normal='1' and MCycle="001" and TState=4 then
                if Exec_Control(EC_MB_WRITE)='1' then MBASE<=ACC;else ACC<=MBASE;end if;
            end if;

        end if;

        end if;

    end process;

---------------------------------------------------------------------------
--
-- BC('), DE('), HL('), IX and IY
--
---------------------------------------------------------------------------
    process (CLK_n)
    begin
        if CLK_n'event and CLK_n = '1' then
            if ClkEn = '1' then
                -- Bus Address_Reg / Write_Decode
                RegAddrA_r <= Alternate & Set_BusA_To(2 downto 1);
                -- R16: delayed byte commit must retain its destination across IRQ/NMI entry.
                -- Reuse the existing registered port address; add no register.
                if XY_Ind = '0' and XY_State /= "00" and Set_BusA_To(2 downto 1) = "10" then
                    RegAddrA_r <= XY_State(1) & "11";
                end if;

                if Pair_Indirect='1' then RegAddrA_r<=Indirect_Index;end if;

                -- Bus B
                RegAddrB_r <= Alternate & Set_BusB_To(2 downto 1);
                if XY_Ind = '0' and XY_State /= "00" and Set_BusB_To(2 downto 1) = "10" then
                    RegAddrB_r <= XY_State(1) & "11";
                end if;

                -- Address from register
                RegAddrC_Base <= Alternate & Set_Addr_To(1 downto 0);
                -- Jump (HL), LD SP,HL
                if (JumpXY = '1' or LDSPHL = '1') then
                    RegAddrC_Base <= Alternate & "10";
                end if;
                if ((JumpXY = '1' or LDSPHL = '1') and XY_State /= "00") or (MCycle = "110" and Ctrl_Stack='0' and Block_IO2='0') then
                    RegAddrC_Base <= XY_State(1) & "11";
                end if;

                if I_DJNZ = '1' and Save_ALU_r = '1' and Mode < 2 then
                    IncDecZ <= F_Out(Flag_Z);
                end if;
                if (TState = 2 or (TState = 3 and MCycle = "001")) and IncDec_16(2 downto 0) = "100" then
                    if Block_Long='1' then
                        IncDecZ <= not Block_Result_Zero;
                    elsif ID16 = 0 then
                        IncDecZ <= '0';
                    else
                        IncDecZ <= '1';
                    end if;
                end if;

                RegBusA_r <= RegBusA;
            end if;
        end if;
    end process;

    RegAddrA <= Indirect_Index when Pair_Indirect='1' else EA_Target when LEA_Commit='1' else Mul_Target when Mul_Active='1' else Arith_Target when Arith_Long='1' else EX_SP_Index when EX_SP_Long='1' else
            -- 16 bit increment/decrement
            Alternate & IncDec_16(1 downto 0) when (TState = 2 or
                (TState = 3 and MCycle = "001" and IncDec_16(2) = '1')) and XY_State = "00" else
            XY_State(1) & "11" when (TState = 2 or
                (TState = 3 and MCycle = "001" and IncDec_16(2) = '1')) and IncDec_16(1 downto 0) = "10" else
            -- EX HL,DL
            Alternate & "10" when ExchangeDH = '1' and TState = 3 else
            Alternate & "01" when ExchangeDH = '1' and TState = 4 else
            -- Bus Address_Reg / Write_Decode
            RegAddrA_r;

    RegAddrB <= Arith_Source when Arith_Long='1' else
            -- EX HL,DL
            Alternate & "01" when ExchangeDH = '1' and TState = 3 else
            -- Bus B
            RegAddrB_r;

    ID16 <= signed(RegBusA) - 1 when IncDec_16(3) = '1' else
            signed(RegBusA) + 1;

    process (Save_ALU_r, Auto_Wait_t1, ALU_OP_r, Read_To_Reg_r,
            ExchangeDH, IncDec_16, MCycle, TState, Wait_n, EX_SP_Result_WE, Arith_Commit, Mul_Reg_Commit, LEA_Commit, IV_Read_Commit)
    begin
        RegWEH <= EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit or LEA_Commit or IV_Read_Commit;
        RegWEL <= EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit or LEA_Commit or IV_Read_Commit;
        if (TState = 1 and Save_ALU_r = '0' and Auto_Wait_t1 = '0') or
            (Save_ALU_r = '1' and ALU_OP_r /= "0111") then
            case Read_To_Reg_r is
            when "10000" | "10001" | "10010" | "10011" | "10100" | "10101" =>
                RegWEH <= not Read_To_Reg_r(0);
                RegWEL <= Read_To_Reg_r(0);
            when others =>
            end case;
        end if;

        if ExchangeDH = '1' and (TState = 3 or TState = 4) then
            RegWEH <= '1';
            RegWEL <= '1';
        end if;

        if IncDec_16(2) = '1' and ((TState = 2 and Wait_n = '1' and MCycle /= "001") or (TState = 3 and MCycle = "001")) then
            case IncDec_16(1 downto 0) is
            when "00" | "01" | "10" =>
                RegWEH <= '1';
                RegWEL <= '1';
            when others =>
            end case;
        end if;
    end process;

    process (Save_Mux, RegBusB, RegBusA_r, ID16,
            ExchangeDH, IncDec_16, MCycle, TState, Wait_n, EX_SP_Result_WE, EX_SP_Read, Arith_Commit, Arith_Result, Mul_Reg_Commit, Mul_Product, LEA_Commit, EA_Result, IV_Read_Commit, I_Upper, I)
    begin
        if IV_Read_Commit='1' then RegDIH<=I_Upper;RegDIL<=I;
        elsif LEA_Commit='1' then RegDIH<=EA_Result(15 downto 8);RegDIL<=EA_Result(7 downto 0);
        elsif Mul_Reg_Commit='1' then RegDIH<=std_logic_vector(Mul_Product(15 downto 8));RegDIL<=std_logic_vector(Mul_Product(7 downto 0));
        elsif Arith_Commit='1' then RegDIH<=std_logic_vector(Arith_Result(15 downto 8));RegDIL<=std_logic_vector(Arith_Result(7 downto 0));
        elsif EX_SP_Result_WE='1' then RegDIH<=EX_SP_Read(15 downto 8);RegDIL<=EX_SP_Read(7 downto 0);
        else RegDIH <= Save_Mux;RegDIL <= Save_Mux;end if;

        if ExchangeDH = '1' and TState = 3 then
            RegDIH <= RegBusB(15 downto 8);
            RegDIL <= RegBusB(7 downto 0);
        end if;
        if ExchangeDH = '1' and TState = 4 then
            RegDIH <= RegBusA_r(15 downto 8);
            RegDIL <= RegBusA_r(7 downto 0);
        end if;

        if IncDec_16(2) = '1' and ((TState = 2 and MCycle /= "001") or (TState = 3 and MCycle = "001")) then
            RegDIH <= std_logic_vector(ID16(15 downto 8));
            RegDIL <= std_logic_vector(ID16(7 downto 0));
        end if;
    end process;

    Reg24DI<=Load_Result when Load_Commit='1' else Upper_Port_Data & RegDIH & RegDIL;
    Reg24Mask<=Load_Mask when Load_Commit='1' and Load_SP='0' else
               "000" when Load_Commit='1' else Upper_Port_WE & RegWEH & RegWEL;
    Reg24AddrW<=Load_Target when Load_Commit='1' else Upper_Port_Index when Upper_Port_WE='1' else RegAddrA;
    Reg24AddrU<=Pair_Upper_Index when Pair_Absolute='1' else Stack_Upper_Index;
    Reg24Exchange<=Exec_Control(EC_DATA_LONG) and ExchangeDH when TState=3 else '0';
    RegBusA<=Reg24A(15 downto 0);
    RegBusB<=Reg24B(15 downto 0);
    RegBusC<=Reg24C(15 downto 0);
    Regs : T80_Reg_eZ80
        port map(
            Clk=>CLK_n, CEN=>ClkEn, RESET_n=>RESET_n,
            WMask=>Reg24Mask, AddrA=>RegAddrA, AddrB=>RegAddrB, AddrC=>RegAddrC,
            AddrU=>Reg24AddrU, AddrW=>Reg24AddrW, DI=>Reg24DI, DOA=>Reg24A, DOB=>Reg24B, DOC=>Reg24C,
            DOU=>Reg24UpperU, Exchange_U=>Reg24Exchange, Alternate=>Alternate,
            Upper_View=>Upper_View);

---------------------------------------------------------------------------
--
-- Buses
--
---------------------------------------------------------------------------
    process (CLK_n)
    begin
        if CLK_n'event and CLK_n = '1' then
            if ClkEn = '1' then
            case Set_BusB_To is
            when "0111" =>
                BusB <= ACC;
            when "0000" | "0001" | "0010" | "0011" | "0100" | "0101" =>
                if Set_BusB_To(0) = '1' then
                    BusB <= RegBusB(7 downto 0);
                else
                    BusB <= RegBusB(15 downto 8);
                end if;
            when "0110" =>
                BusB <= DI_Reg;
            when "1000" =>
                if SP_Readback='1' or (Pair_Absolute='1' and Data_Long='1' and Pair_SP='1') then BusB<=std_logic_vector(SPL(7 downto 0));else BusB <= std_logic_vector(SP(7 downto 0));end if;
            when "1001" =>
                if SP_Readback='1' or (Pair_Absolute='1' and Data_Long='1' and Pair_SP='1') then BusB<=std_logic_vector(SPL(15 downto 8));else BusB <= std_logic_vector(SP(15 downto 8));end if;
            when "1010" =>
                BusB <= "00000001";
            when "1011" =>
                BusB <= F;
            when "1100" =>
                BusB <= std_logic_vector(PC(7 downto 0));
            when "1101" =>
                BusB <= std_logic_vector(PC(15 downto 8));
            when "1110" =>
                if EX_SP_Long='1' then BusB<=Reg24A(23 downto 16);
                elsif Pair_Absolute='1' then
                    if Pair_SP='1' then BusB<=std_logic_vector(SPL(23 downto 16));else BusB<=Reg24UpperU;end if;
                elsif SP_Readback='1' then BusB<=std_logic_vector(SPL(23 downto 16));else BusB <= "00000000";end if;
            when others =>
                BusB <= "--------";
            end case;

            case Set_BusA_To is
            when "0111" =>
                BusA <= ACC;
            when "0000" | "0001" | "0010" | "0011" | "0100" | "0101" =>
                if Set_BusA_To(0) = '1' then
                    BusA <= RegBusA(7 downto 0);
                else
                    BusA <= RegBusA(15 downto 8);
                end if;
            when "0110" =>
                BusA <= DI_Reg;
            when "1000" =>
                BusA <= std_logic_vector(SP(7 downto 0));
            when "1001" =>
                BusA <= std_logic_vector(SP(15 downto 8));
            when "1010" =>
                BusA <= "00000000";
            when "1100" =>
                BusA <= TmpAddr(7 downto 0); -- R25: retained TSTIO immediate, no new data FF.
            when others =>
                BusB <= "--------";
            end case;
            if XYbit_undoc='1' then
                BusA <= DI_Reg;
                BusB <= DI_Reg;
            end if;
            end if;
        end if;
    end process;

---------------------------------------------------------------------------
--
-- Generate external control signals
--
---------------------------------------------------------------------------
    process (RESET_n,CLK_n)
    begin
        if RESET_n = '0' then
            RFSH_n <= '1';
        elsif CLK_n'event and CLK_n = '1' then
            if CEN = '1' then
            if MCycle = "001" and ((TState = 2  and Wait_n = '1') or TState = 3) then
                RFSH_n <= '0';
            else
                RFSH_n <= '1';
            end if;
            end if;
        end if;
    end process;

    MC<="001" when Frame_Active='1' and Frame_TS=4 else "010" when Frame_Active='1' else std_logic_vector(MCycle);
    TS<=std_logic_vector(Frame_TS) when Frame_Active='1' else std_logic_vector(TState);
    DI_Reg <= DI;
    HALT_n<='0' when Frame_State=frame_fault else not Halt_FF;
    BUSAK_n <= not BusAck;
    IntCycle_n<='1' when Frame_Active='1' else not IntCycle;
    IntE <= IntE_FF1;
    IORQ<='0' when Frame_Active='1' else IORQ_i;
    Stop <= I_DJNZ;

-------------------------------------------------------------------------
--
-- Syncronise inputs
--
-------------------------------------------------------------------------
    process (RESET_n, CLK_n)
        variable OldNMI_n : std_logic;
    begin
        if RESET_n = '0' then
            BusReq_s <= '0';
            INT_s <= '0';
            NMI_s <= '0';
            OldNMI_n := '0';
        elsif CLK_n'event and CLK_n = '1' then
            if CEN = '1' then
            BusReq_s <= not BUSRQ_n;
            INT_s <= not INT_n;

            if ADL_Mode='1' or MADL='1' or Frame_Active='1' then
                if NMI_n='0' and OldNMI_n='1' then NMI_s<='1';
                elsif NMI_Accept='1' then NMI_s<='0';end if;
            else
                if NMICycle='1' then NMI_s<='0';
                elsif NMI_n='0' and OldNMI_n='1' then NMI_s<='1';end if;
            end if;
            OldNMI_n := NMI_n;
            end if;
        end if;
    end process;

-------------------------------------------------------------------------
--
-- Main state machine
--
-------------------------------------------------------------------------
    process (RESET_n, CLK_n)
    begin
        if RESET_n = '0' then
            MCycle <= "001";
            TState <= "000";
            Pre_XY_F_M <= "000";
            Halt_FF <= '0';
            BusAck <= '0';
            NMICycle <= '0';
            IntCycle <= '0';
            IntE_FF1 <= '0';
            IntE_FF2 <= '0';
            No_BTR <= '0';
            Auto_Wait_t1 <= '0';
            Auto_Wait_t2 <= '0';
            M1_n <= '1';
        elsif CLK_n'event and CLK_n = '1' then
            if CEN = '1' then
            if Frame_Active='1' then
                if Frame_End='1' then
                    MCycle<="001";TState<="001";M1_n<='0';IntCycle<='0';NMICycle<='0';
                    Auto_Wait_t1<='0';Auto_Wait_t2<='0';No_BTR<='0';
                    if Frame_Returning='1' and Frame_RetN='1' then IntE_FF1<=IntE_FF2;end if;
                    if NMI_s='1' then NMICycle<='1';IntE_FF1<='0';IntE_FF2<=Frame_IEF;
                    elsif (Frame_Returning='1' or Frame_Is_Call='1') and Frame_IEF='1' and INT_s='1' and (IStatus/="11") then
                        IntCycle<='1';IntE_FF1<='0';IntE_FF2<='0';
                    end if;
                end if;
            elsif Frame_Ready='1' then
                if BusAck='1' and BusReq_s='0' then BusAck<='0';end if;
            else
            if T_Res = '1' then
                Auto_Wait_t1 <= '0';
            else
                Auto_Wait_t1 <= Auto_Wait or IORQ_i;
            end if;
            Auto_Wait_t2 <= Auto_Wait_t1;
            No_BTR <= (I_BT and (not IR(4) or not F(Flag_P))) or
                    (I_BC and (not IR(4) or F(Flag_Z) or not F(Flag_P))) or
                    (I_BTR and (not IR(4) or F(Flag_Z)));
            if TState = 2 then
                if SetEI = '1' then
                    IntE_FF1 <= '1';
                    IntE_FF2 <= '1';
                end if;
                if I_RETN = '1' then
                    IntE_FF1 <= IntE_FF2;
                end if;
            end if;
            if TState = 3 then
                if SetDI = '1' then
                    IntE_FF1 <= '0';
                    IntE_FF2 <= '0';
                end if;
            end if;
            if IRQ_Return='1' and Exec_Control(EC_RETN_OPCODE)='1' and MCycle="100" and T_Res='1' then IntE_FF1<=IntE_FF2;end if;
            if IntCycle = '1' or NMICycle = '1' then
                Halt_FF <= '0';
            end if;
            if MCycle = "001" and TState = 2 and Wait_n = '1' then
                M1_n <= '1';
            end if;
            if BusReq_s = '1' and BusAck = '1' then
            else
                BusAck <= '0';
                if TState = 2 and Wait_n = '0' then
                elsif T_Res = '1' then
                    if Halt = '1' then
                        Halt_FF <= '1';
                    end if;
                    if BusReq_s = '1' then
                        BusAck <= '1';
                    else
                        TState <= "001";
                        if NextIs_XY_Fetch = '1' then
                            MCycle <= "110";
                            Pre_XY_F_M <= MCycle;
                            if Exec_Control(EC_LD_MEM_IMM)='1' and Mode = 0 then
                                Pre_XY_F_M <= "010";
                            end if;
                        elsif (MCycle = "111" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0') or
                            (MCycle = "110" and Mode = 1 and ISet /= "01" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0') then
                            MCycle <= std_logic_vector(unsigned(Pre_XY_F_M) + 1);
                        elsif (MCycle = MCycles) or
                            No_BTR = '1' or
                            (MCycle = "010" and I_DJNZ = '1' and IncDecZ = '1') then
                            M1_n <= '0';
                            MCycle <= "001";
                            IntCycle <= '0';
                            NMICycle <= '0';
                            if NMI_s = '1' and Prefix = "00" and Width_Pending='0' then
                                NMICycle <= '1';
                                if ADL_Mode='1' or MADL='1' or Frame_Active='1' then IntE_FF2<=Effective_IEF;end if;
                                IntE_FF1 <= '0';
                            elsif ((ADL_Mode='0' and MADL='0') or IStatus/="11") and (Effective_IEF = '1' and INT_s = '1') and Prefix = "00" and Width_Pending='0' and SetEI = '0' then
                                IntCycle <= '1';
                                IntE_FF1 <= '0';
                                IntE_FF2 <= '0';
                            end if;
                        else
                            MCycle <= std_logic_vector(unsigned(MCycle) + 1);
                        end if;
                    end if;
                else
                    if (Auto_Wait = '1' and Auto_Wait_t2 = '0') nor
                        (IOWait = 1 and IORQ_i = '1' and Auto_Wait_t1 = '0') then
                        TState <= TState + 1;
                    end if;
                end if;
            end if;
            if TState = 0 then
                M1_n <= '0';
            end if;
            end if;
            end if;
        end if;
    end process;

    process (IntCycle, NMICycle, MCycle)
    begin
        Auto_Wait <= '0';
        if IntCycle = '1' or NMICycle = '1' then
            if MCycle = "001" then
                Auto_Wait <= '1';
            end if;
        end if;
    end process;

end;
