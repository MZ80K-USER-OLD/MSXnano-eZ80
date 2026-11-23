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
--  0250 : Version alignment by KdL 2017.10.23
--
--  +k01 : Version alignment by KdL 2010.10.25
--  +k02 : Added R800_mode signal by KdL 2018.05.14
--  +k03 : Version alignment by KdL 2019.05.20
--  +k04 : Separation of T800 from T80_eZ80 by KdL 2021.02.01
--

library IEEE;
use IEEE.std_logic_1164.all;

package T80_eZ80_Pack is
    -- R24: instruction-static execution descriptor, captured with IR.
    subtype exec_control_t is std_logic_vector(52 downto 0);
    constant EC_EX_SP : natural := 0;
    constant EC_STACK : natural := 1;
    constant EC_INCDEC : natural := 2;
    constant EC_BYTE_ABS : natural := 3;
    constant EC_PAIR_ABS : natural := 4;
    constant EC_PAIR_IND : natural := 5;
    constant EC_ARITH : natural := 6;
    constant EC_PAIR_INDEX : natural := 7;
    constant EC_BLOCK : natural := 8;
    constant EC_MUL : natural := 9;
    constant EC_EA : natural := 10;
    constant EC_PEA : natural := 11;
    constant EC_JP : natural := 12;
    constant EC_NATIVE_CTRL : natural := 13;
    constant EC_IRQ_RETURN : natural := 14;
    constant EC_IV_READ : natural := 15;
    constant EC_TST : natural := 16;
    constant EC_IO2 : natural := 17;
    constant EC_SP_READ : natural := 18;
    constant EC_EXT_MODE0 : natural := 19;
    constant EC_WIDTH_PREFIX : natural := 20;
    constant EC_IMM_LONG : natural := 21;
    constant EC_ADL_ED_ALIAS : natural := 22;
    constant EC_MIX_CTRL : natural := 23;
    constant EC_MIX_SUPPORTED : natural := 24;
    constant EC_IV_PAIR : natural := 25;
    constant EC_MB_OPCODE : natural := 26;
    constant EC_MADL_OPCODE : natural := 27;
    constant EC_MIX_IRQ_RETURN : natural := 28;
    constant EC_EXT_BASE : natural := 29;
    constant EC_ANY_LONG : natural := 30;
    constant EC_ED_NO_WRITE : natural := 31;
    constant EC_EXT : natural := 32;
    constant EC_FRAME_CALL : natural := 33;
    constant EC_FRAME_RET : natural := 34;
    constant EC_FRAME_IRQ_RET : natural := 35;
    constant EC_FRAME_RST : natural := 36;
    constant EC_RST_WIDTH_OK : natural := 37;
    constant EC_RST_WIDTH_BAD : natural := 38;
    constant EC_DATA_LONG : natural := 39;
    constant EC_MB_VALID : natural := 40;
    constant EC_IV_WRITE : natural := 41;
    constant EC_EXPLICIT_WIDTH : natural := 42;
    constant EC_ADL_SNAPSHOT : natural := 43;
    constant EC_CALL_KIND:natural:=44;
    constant EC_RET_KIND:natural:=45;
    constant EC_RST_KIND:natural:=46;
    constant EC_UNCOND_FLOW:natural:=47;
    constant EC_JP_ALWAYS:natural:=48;
    constant EC_RETN_OPCODE:natural:=49;
    constant EC_LOAD_IMM:natural:=50;
    constant EC_LOAD_ABS:natural:=51;
    constant EC_LOAD_IND:natural:=52;
    function Decode_Execution(op: std_logic_vector(7 downto 0); pg, xy: std_logic_vector(1 downto 0); ex, adl, dl, sl, hw: std_logic; mode_id: integer) return exec_control_t;
    function Classify_Write(op : std_logic_vector(7 downto 0)) return std_logic_vector;

    component T80_eZ80
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
    end component;

    component T80_Reg_eZ80
    port(
        Clk, CEN, RESET_n : in std_logic;
        WMask : in std_logic_vector(2 downto 0);
        AddrA, AddrB, AddrC, AddrU, AddrW : in std_logic_vector(2 downto 0);
        DI : in std_logic_vector(23 downto 0);
        DOA, DOB, DOC : out std_logic_vector(23 downto 0);
        DOU : out std_logic_vector(7 downto 0);
        Exchange_U, Alternate : in std_logic;
        Upper_View : out std_logic_vector(63 downto 0)
    );
    end component;

    component T80_MCode_eZ80
    generic(
        Mode        : integer := 0;
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
        IR          : in std_logic_vector(7 downto 0);
        Write_Class : in std_logic_vector(7 downto 0);
                Exec_Control : in exec_control_t;
                Interrupt_Long : in std_logic;
                Ext_Active, Data_Long, Stream_Long, ADL_Mode, Has_Width : in std_logic;
                Flow_Cond : out std_logic;
                Branch_Condition : in std_logic;
                Interrupt_Mode : in std_logic_vector(1 downto 0);
        ISet        : in std_logic_vector(1 downto 0);
        MCycle      : in std_logic_vector(2 downto 0);
        F           : in std_logic_vector(7 downto 0);
        NMICycle    : in std_logic;
        IntCycle    : in std_logic;
        XY_State    : in  std_logic_vector(1 downto 0);
        MCycles     : out std_logic_vector(2 downto 0);
        TStates     : out std_logic_vector(2 downto 0);
        Prefix      : out std_logic_vector(1 downto 0); -- None,BC,ED,DD/FD
        Inc_PC      : out std_logic;
        Inc_WZ      : out std_logic;
        IncDec_16   : out std_logic_vector(3 downto 0); -- BC,DE,HL,SP   0 is inc
        Read_To_Reg : out std_logic;
        Read_To_Acc : out std_logic;
        Set_BusA_To : out std_logic_vector(3 downto 0); -- B,C,D,E,H,L,DI/DB,A,SP(L),SP(M),0,F
        Set_BusB_To : out std_logic_vector(3 downto 0); -- B,C,D,E,H,L,DI,A,SP(L),SP(M),1,F,PC(L),PC(M),0
        ALU_Op      : out std_logic_vector(3 downto 0);
            -- ADD, ADC, SUB, SBC, AND, XOR, OR, CP, ROT, BIT, SET, RES, DAA, RLD, RRD, None
        ALU_cpi     : out std_logic;
        Save_ALU    : out std_logic;
        PreserveC   : out std_logic;
        Arith16     : out std_logic;
        Set_Addr_To : out std_logic_vector(2 downto 0); -- aNone,aXY,aIOA,aSP,aBC,aDE,aZI
        IORQ        : out std_logic;
        Jump        : out std_logic;
        JumpE       : out std_logic;
        JumpXY      : out std_logic;
        Call        : out std_logic;
        RstP        : out std_logic;
        LDZ         : out std_logic;
        LDW         : out std_logic;
        LDSPHL      : out std_logic;
        Special_LD  : out std_logic_vector(2 downto 0); -- A,I;A,R;I,A;R,A;None
        ExchangeDH  : out std_logic;
        ExchangeRp  : out std_logic;
        ExchangeAF  : out std_logic;
        ExchangeRS  : out std_logic;
        I_DJNZ      : out std_logic;
        I_CPL       : out std_logic;
        I_CCF       : out std_logic;
        I_SCF       : out std_logic;
        I_RETN      : out std_logic;
        I_BT        : out std_logic;
        I_BC        : out std_logic;
        I_BTR       : out std_logic;
        I_RLD       : out std_logic;
        I_RRD       : out std_logic;
        I_INRC      : out std_logic;
        SetDI       : out std_logic;
        SetEI       : out std_logic;
        IMode       : out std_logic_vector(1 downto 0);
        Halt        : out std_logic;
        NoRead      : out std_logic;
        Write       : out std_logic;
        XYbit_undoc : out std_logic
    );
    end component;

    component T80_ALU_eZ80
    generic(
        Mode        : integer := 0;
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
        Arith16     : in std_logic;
        Z16         : in std_logic;
        ALU_cpi     : in std_logic;
        ALU_Op      : in std_logic_vector(3 downto 0);
        IR          : in std_logic_vector(5 downto 0);
        ISet        : in std_logic_vector(1 downto 0);
        BusA        : in std_logic_vector(7 downto 0);
        BusB        : in std_logic_vector(7 downto 0);
        F_In        : in std_logic_vector(7 downto 0);
        Q           : out std_logic_vector(7 downto 0);
        F_Out       : out std_logic_vector(7 downto 0)
    );
    end component;

end;

package body T80_eZ80_Pack is
    function Classify_Opcode(op : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable c : std_logic_vector(15 downto 0) := (others=>'0');
    begin
        if op=x"E3" then c(0):='1';end if;
        if op(7 downto 6)="11" and (op(3 downto 0)="0101" or op(3 downto 0)="0001") then c(1):='1';end if;
        if op(7 downto 6)="00" and (op(3 downto 0)="0011" or op(3 downto 0)="1011") then c(2):='1';end if;
        if op=x"32" or op=x"3A" then c(3):='1';end if;
        if op=x"22" or op=x"2A" then c(4):='1';end if;
        if op(7 downto 6)="01" and op(2 downto 0)="011" then c(5):='1';end if;
        if op(7 downto 6)="00" and op(3 downto 0)="1001" then c(6):='1';end if;
        if op(7 downto 6)="01" and op(2 downto 0)="010" then c(7):='1';end if;
        if (op(7 downto 5)="101" and op(2 downto 1)="00") or op=x"84" or op=x"8C" or op=x"A4" or op=x"AC" then c(8):='1';end if;
        if op(7 downto 6)="01" and op(3 downto 0)="1100" then c(9):='1';end if;
        if op=x"02" or op=x"03" or op=x"12" or op=x"13" or op=x"22" or op=x"23" or
           op=x"32" or op=x"33" or op=x"54" or op=x"55" or op=x"65" or op=x"66" then c(10):='1';end if;
        if op=x"65" or op=x"66" then c(11):='1';end if;
        if op=x"C3" or (op(7 downto 6)="11" and op(2 downto 0)="010") then c(12):='1';end if;
        if op=x"CD" or op=x"C9" or (op(7 downto 6)="11" and
           (op(2 downto 0)="100" or op(2 downto 0)="000" or op(2 downto 0)="111")) then c(13):='1';end if;
        if op=x"45" or op=x"4D" then c(14):='1';end if;
        if op=x"D7" then c(15):='1';end if;
        return c;
    end function;
    function Decode_Execution(op: std_logic_vector(7 downto 0); pg, xy: std_logic_vector(1 downto 0); ex, adl, dl, sl, hw: std_logic; mode_id: integer) return exec_control_t is
        variable raw:std_logic_vector(15 downto 0);
        variable w:std_logic_vector(7 downto 0);
        variable c:exec_control_t := (others=>'0');
    begin
        raw:=Classify_Opcode(op);w:=Classify_Write(op);
        if ex='1' and dl='1' and pg="00" and raw(0)='1' then c(EC_EX_SP):='1';end if;
        if ex='1' and dl='1' and pg="00" and raw(1)='1' then c(EC_STACK):='1';end if;
        if ex='1' and dl='1' and pg="00" and raw(2)='1' then c(EC_INCDEC):='1';end if;
        if ex='1' and (dl='1' or sl='1') and pg="00" and raw(3)='1' then c(EC_BYTE_ABS):='1';end if;
        if ex='1' and (dl='1' or sl='1') and ((pg="00" and raw(4)='1') or (pg="10" and raw(5)='1')) then c(EC_PAIR_ABS):='1';end if;
        if mode_id=0 and ex='1' and (pg="10" or (pg="00" and xy/="00")) and (w(7 downto 4)=x"A" or w(7 downto 4)=x"B") then c(EC_PAIR_IND):='1';end if;
        if mode_id=0 and ex='1' and dl='1' and ((pg="00" and raw(6)='1') or (pg="10" and raw(7)='1')) then c(EC_ARITH):='1';end if;
        if mode_id=0 and ex='1' and pg="00" and xy/="00" and (w(7 downto 4)=x"A" or w(7 downto 4)=x"B") then c(EC_PAIR_INDEX):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and raw(8)='1' then c(EC_BLOCK):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and raw(9)='1' then c(EC_MUL):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and raw(10)='1' then c(EC_EA):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and raw(10)='1' and raw(11)='1' then c(EC_PEA):='1';end if;
        if ex='1' and pg="00" and raw(12)='1' and dl=sl then c(EC_JP):='1';end if;
        if ex='1' and adl='1' and hw='0' and pg="00" and raw(13)='1' then c(EC_NATIVE_CTRL):='1';end if;
        if ex='1' and adl='1' and hw='0' and pg="10" and raw(14)='1' then c(EC_IRQ_RETURN):='1';end if;
        if ex='1' and pg="10" and raw(15)='1' then c(EC_IV_READ):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and ((op(7 downto 6)="00" and op(2 downto 0)="100") or op=x"64") then c(EC_TST):='1';end if;
        if mode_id=0 and ex='1' and pg="10" and w(7 downto 4)=x"C" then c(EC_IO2):='1';end if;
        if pg="10" and op=x"73" and dl='1' and sl='0' then c(EC_SP_READ):='1';end if;
        if ex='1' and mode_id=0 then c(EC_EXT_MODE0):='1';end if;
        if ex='1' and mode_id=0 and pg="00" and (op=x"40" or op=x"49" or op=x"52" or op=x"5B") then c(EC_WIDTH_PREFIX):='1';end if;
        if ex='1' and mode_id=0 and pg="00" and op(7 downto 6)="00" and op(3 downto 0)="0001" and sl='1' then c(EC_IMM_LONG):='1';end if;
        if adl='1' and pg="10" and w(7 downto 4)=x"7" then c(EC_ADL_ED_ALIAS):='1';end if;
        if ex='1' and hw='1' and pg="00" and raw(13)='1' then c(EC_MIX_CTRL):='1';end if;
        if mode_id=0 and ((((op=x"CD" or op(2 downto 0)="100")) and dl=adl) or ((op=x"C9" or op(2 downto 0)="000") and dl='1')) then c(EC_MIX_SUPPORTED):='1';end if;
        if ex='1' and pg="10" and (op=x"C7" or op=x"D7") then c(EC_IV_PAIR):='1';end if;
        if ex='1' and mode_id=0 and pg="10" and (op=x"6D" or op=x"6E") then c(EC_MB_OPCODE):='1';end if;
        if ex='1' and mode_id=0 and pg="10" and (op=x"7D" or op=x"7E") then c(EC_MADL_OPCODE):='1';end if;
        if ex='1' and hw='1' and pg="10" and raw(14)='1' then c(EC_MIX_IRQ_RETURN):='1';end if;
        if ex='1' and pg="00" then c(EC_EXT_BASE):='1';end if;
        if dl='1' or sl='1' then c(EC_ANY_LONG):='1';end if;
        if ex='1' and pg="10" and (w(7 downto 4)=x"9" or (w(7 downto 4)=x"8" and (adl='1' or hw='1'))) then c(EC_ED_NO_WRITE):='1';end if;
        if ex='1' then c(EC_EXT):='1';end if;
        if mode_id=0 and pg="00" and hw='1' and dl=adl and w(3 downto 1)="101" then c(EC_FRAME_CALL):='1';end if;
        if mode_id=0 and pg="00" and hw='1' and dl='1' and w(3 downto 1)="110" then c(EC_FRAME_RET):='1';end if;
        if pg="10" and hw='1' and dl='1' and raw(14)='1' then c(EC_FRAME_IRQ_RET):='1';end if;
        if mode_id=0 and pg="00" and w(3 downto 0)=x"E" then c(EC_FRAME_RST):='1';end if;
        if hw='1' and sl=adl then c(EC_RST_WIDTH_OK):='1';end if;
        if hw='1' and sl/=adl then c(EC_RST_WIDTH_BAD):='1';end if;
        if ex='1' and dl='1' then c(EC_DATA_LONG):='1';end if;
        if ex='1' and adl='1' and pg="10" and mode_id=0 and (op=x"6D" or op=x"6E") then c(EC_MB_VALID):='1';end if;
        if ex='1' and pg="10" and op=x"C7" then c(EC_IV_WRITE):='1';end if;
        if hw='1' then c(EC_EXPLICIT_WIDTH):='1';end if;
        if adl='1' then c(EC_ADL_SNAPSHOT):='1';end if;
        if op=x"CD" or op(2 downto 0)="100" then c(EC_CALL_KIND):='1';end if;
        if op=x"C9" or op(2 downto 0)="000" then c(EC_RET_KIND):='1';end if;
        if op(2 downto 0)="111" then c(EC_RST_KIND):='1';end if;
        if op=x"CD" or op=x"C9" then c(EC_UNCOND_FLOW):='1';end if;
        if op=x"C3" then c(EC_JP_ALWAYS):='1';end if;
        if op=x"45" then c(EC_RETN_OPCODE):='1';end if;
        -- R24.2: terminal-opcode qualifiers for the common pair-load collector.
        if mode_id=0 and ex='1' then
            if pg="00" and op(7 downto 6)="00" and op(3 downto 0)="0001" and c(EC_PAIR_INDEX)='0' then c(EC_LOAD_IMM):='1';end if;
            if op(3)='1' and ((pg="00" and raw(4)='1') or (pg="10" and raw(5)='1')) then c(EC_LOAD_ABS):='1';end if;
            if c(EC_PAIR_IND)='1' and w(7 downto 4)=x"B" then c(EC_LOAD_IND):='1';end if;
        end if;
        return c;
    end function;

    -- R11.7: raw opcode classification, captured alongside every IR update.
    -- Low nibble is the unprefixed class; high nibble is the ED class.
    function Classify_Write(op : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable c : std_logic_vector(7 downto 0) := x"00";
    begin
        if op=x"22" then c(3 downto 0):=x"1";
        elsif op=x"2A" then c(3 downto 0):=x"2";
        elsif op=x"32" then c(3 downto 0):=x"3";
        elsif op=x"3A" then c(3 downto 0):=x"4";
        elsif op(7 downto 6)="11" and op(3 downto 0)="0101" then c(3 downto 0):=x"5";
        elsif op(7 downto 6)="11" and op(3 downto 0)="0001" then c(3 downto 0):=x"6";
        elsif op=x"E3" then c(3 downto 0):=x"7";
        elsif op(7 downto 6)="00" and op(3 downto 0)="1001" then c(3 downto 0):=x"8";
        elsif op=x"C3" or (op(7 downto 6)="11" and op(2 downto 0)="010") then c(3 downto 0):=x"9";
        elsif op=x"CD" then c(3 downto 0):=x"A";
        elsif op(7 downto 6)="11" and op(2 downto 0)="100" then c(3 downto 0):=x"B";
        elsif op=x"C9" then c(3 downto 0):=x"C";
        elsif op(7 downto 6)="11" and op(2 downto 0)="000" then c(3 downto 0):=x"D";
        elsif op(7 downto 6)="11" and op(2 downto 0)="111" then c(3 downto 0):=x"E";
        end if;
        if op(7 downto 6)="01" and op(2 downto 0)="011" then
            if op(3)='0' then c(7 downto 4):=x"1";else c(7 downto 4):=x"2";end if;
        elsif op(7 downto 6)="01" and op(2 downto 0)="010" then c(7 downto 4):=x"3";
        elsif op(7 downto 6)="01" and op(3 downto 0)="1100" then c(7 downto 4):=x"4";
        elsif op=x"65" or op=x"66" then c(7 downto 4):=x"6";
        elsif op=x"02" or op=x"03" or op=x"12" or op=x"13" or op=x"22" or op=x"23" or
              op=x"32" or op=x"33" or op=x"54" or op=x"55" then c(7 downto 4):=x"5";
        elsif op=x"5D" or op=x"6D" or op=x"75" or op=x"7D" then c(7 downto 4):=x"7";
        elsif op=x"45" or op=x"4D" then c(7 downto 4):=x"8";
        elsif op=x"C7" or op=x"D7" then c(7 downto 4):=x"9";
        end if;
        if op=x"84" or op=x"8C" or op=x"A4" or op=x"AC" then c(7 downto 4):=x"C";end if;
        -- R16: reuse the existing registered write-class field.
        if op=x"0F" or op=x"1F" or op=x"2F" or op=x"3F" or op=x"3E" then c(7 downto 4):=x"A";
        elsif op=x"07" or op=x"17" or op=x"27" or op=x"37" or op=x"31" then c(7 downto 4):=x"B";end if;
        return c;
    end function;
end package body;
