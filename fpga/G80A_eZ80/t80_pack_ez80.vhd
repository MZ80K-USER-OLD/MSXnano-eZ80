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
    -- R32: compact main-opcode classes, captured with IR.
    subtype base_group_t is std_logic_vector(5 downto 0);
    constant BG_00:base_group_t:="000000";
    constant BG_01:base_group_t:="000001";
    constant BG_02:base_group_t:="000010";
    constant BG_03:base_group_t:="000011";
    constant BG_04:base_group_t:="000100";
    constant BG_05:base_group_t:="000101";
    constant BG_06:base_group_t:="000110";
    constant BG_07:base_group_t:="000111";
    constant BG_08:base_group_t:="001000";
    constant BG_09:base_group_t:="001001";
    constant BG_10:base_group_t:="001010";
    constant BG_11:base_group_t:="001011";
    constant BG_12:base_group_t:="001100";
    constant BG_13:base_group_t:="001101";
    constant BG_14:base_group_t:="001110";
    constant BG_15:base_group_t:="001111";
    constant BG_16:base_group_t:="010000";
    constant BG_17:base_group_t:="010001";
    constant BG_18:base_group_t:="010010";
    constant BG_19:base_group_t:="010011";
    constant BG_20:base_group_t:="010100";
    constant BG_21:base_group_t:="010101";
    constant BG_22:base_group_t:="010110";
    constant BG_23:base_group_t:="010111";
    constant BG_24:base_group_t:="011000";
    constant BG_25:base_group_t:="011001";
    constant BG_26:base_group_t:="011010";
    constant BG_27:base_group_t:="011011";
    constant BG_28:base_group_t:="011100";
    constant BG_29:base_group_t:="011101";
    constant BG_30:base_group_t:="011110";
    constant BG_31:base_group_t:="011111";
    constant BG_32:base_group_t:="100000";
    constant BG_33:base_group_t:="100001";
    constant BG_34:base_group_t:="100010";
    constant BG_35:base_group_t:="100011";
    constant BG_36:base_group_t:="100100";
    constant BG_37:base_group_t:="100101";
    constant BG_38:base_group_t:="100110";
    constant BG_39:base_group_t:="100111";
    constant BG_40:base_group_t:="101000";
    constant BG_41:base_group_t:="101001";
    constant BG_42:base_group_t:="101010";
    constant BG_43:base_group_t:="101011";
    constant BG_44:base_group_t:="101100";
    constant BG_45:base_group_t:="101101";
    constant BG_46:base_group_t:="101110";
    constant BG_47:base_group_t:="101111";
    constant BG_48:base_group_t:="110000";
    constant BG_49:base_group_t:="110001";
    constant BG_50:base_group_t:="110010";
    constant BG_51:base_group_t:="110011";
    constant BG_52:base_group_t:="110100";
    constant BG_53:base_group_t:="110101";
    constant BG_54:base_group_t:="110110";
    constant BG_55:base_group_t:="110111";
    constant BG_56:base_group_t:="111000";
    constant BG_57:base_group_t:="111001";
    constant BG_58:base_group_t:="111010";
    function Decode_Base_Group(op:std_logic_vector(7 downto 0)) return base_group_t;
    subtype cb_group_t is std_logic_vector(2 downto 0);
    constant CG_00:cb_group_t:="000";
    constant CG_01:cb_group_t:="001";
    constant CG_02:cb_group_t:="010";
    constant CG_03:cb_group_t:="011";
    constant CG_04:cb_group_t:="100";
    constant CG_05:cb_group_t:="101";
    constant CG_06:cb_group_t:="110";
    constant CG_07:cb_group_t:="111";
    function Decode_CB_Group(op:std_logic_vector(7 downto 0)) return cb_group_t;
    subtype ed_group_t is std_logic_vector(4 downto 0);
    constant EG_00:ed_group_t:="00000";
    constant EG_01:ed_group_t:="00001";
    constant EG_02:ed_group_t:="00010";
    constant EG_03:ed_group_t:="00011";
    constant EG_04:ed_group_t:="00100";
    constant EG_05:ed_group_t:="00101";
    constant EG_06:ed_group_t:="00110";
    constant EG_07:ed_group_t:="00111";
    constant EG_08:ed_group_t:="01000";
    constant EG_09:ed_group_t:="01001";
    constant EG_10:ed_group_t:="01010";
    constant EG_11:ed_group_t:="01011";
    constant EG_12:ed_group_t:="01100";
    constant EG_13:ed_group_t:="01101";
    constant EG_14:ed_group_t:="01110";
    constant EG_15:ed_group_t:="01111";
    constant EG_16:ed_group_t:="10000";
    constant EG_17:ed_group_t:="10001";
    constant EG_18:ed_group_t:="10010";
    constant EG_19:ed_group_t:="10011";
    constant EG_20:ed_group_t:="10100";
    constant EG_21:ed_group_t:="10101";
    constant EG_22:ed_group_t:="10110";
    constant EG_23:ed_group_t:="10111";
    constant EG_24:ed_group_t:="11000";
    constant EG_25:ed_group_t:="11001";
    constant EG_26:ed_group_t:="11010";
    constant EG_27:ed_group_t:="11011";
    function Decode_ED_Group(op:std_logic_vector(7 downto 0)) return ed_group_t;
    -- R24: instruction-static execution descriptor, captured with IR.
    subtype exec_control_t is std_logic_vector(72 downto 0);
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
    constant EC_TSTIO:natural:=53;
    -- R30: instruction-static selectors, captured at the existing IR edge.
    constant EC_PAGE_BASE:natural:=54;
    constant EC_PAGE_ED:natural:=55;
    constant EC_IND_OPPOSITE:natural:=56;
    constant EC_EA_SOURCE_IY:natural:=57;
    constant EC_EA_TARGET_IX:natural:=58;
    constant EC_EA_TARGET_IY:natural:=59;
    constant EC_JP_INDIRECT:natural:=60;
    constant EC_SP_IMMEDIATE:natural:=61;
    -- R31: shared operand classes and execution subtypes.
    constant EC_PAIR_HL:natural:=62;
    constant EC_PAIR_SP:natural:=63;
    constant EC_STACK_PUSH:natural:=64;
    constant EC_STACK_POP:natural:=65;
    constant EC_BYTE_STORE:natural:=66;
    constant EC_IMM_PAIR:natural:=67;
    constant EC_INDEX_FETCH:natural:=68;
    constant EC_MADL_SET:natural:=69;
    constant EC_MB_WRITE:natural:=70;
    constant EC_LD_MEM_IMM:natural:=71;
    constant EC_ABS_SP:natural:=72;
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
                        Base_Group : in base_group_t;
                CB_Group : in cb_group_t;
                ED_Group : in ed_group_t;
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

    function Decode_Base_Group(op:std_logic_vector(7 downto 0)) return base_group_t is
        variable opcode_bits:bit_vector(7 downto 0);
    begin
        opcode_bits:=to_bitvector(op);
        case opcode_bits is
        when "01000000"|"01000001"|"01000010"|"01000011"|"01000100"|"01000101"|"01000111"
                        |"01001000"|"01001001"|"01001010"|"01001011"|"01001100"|"01001101"|"01001111"
                        |"01010000"|"01010001"|"01010010"|"01010011"|"01010100"|"01010101"|"01010111"
                        |"01011000"|"01011001"|"01011010"|"01011011"|"01011100"|"01011101"|"01011111"
                        |"01100000"|"01100001"|"01100010"|"01100011"|"01100100"|"01100101"|"01100111"
                        |"01101000"|"01101001"|"01101010"|"01101011"|"01101100"|"01101101"|"01101111"
                        |"01111000"|"01111001"|"01111010"|"01111011"|"01111100"|"01111101"|"01111111" => return BG_00;
        when "00000110"|"00001110"|"00010110"|"00011110"|"00100110"|"00101110"|"00111110" => return BG_01;
        when "01000110"|"01001110"|"01010110"|"01011110"|"01100110"|"01101110"|"01111110" => return BG_02;
        when "01110000"|"01110001"|"01110010"|"01110011"|"01110100"|"01110101"|"01110111" => return BG_03;
        when "00110110" => return BG_04;
        when "00001010" => return BG_05;
        when "00011010" => return BG_06;
        when "00111010" => return BG_07;
        when "00000010" => return BG_08;
        when "00010010" => return BG_09;
        when "00110010" => return BG_10;
        when "00000001"|"00010001"|"00100001"|"00110001" => return BG_11;
        when "00101010" => return BG_12;
        when "00100010" => return BG_13;
        when "11111001" => return BG_14;
        when "11000101"|"11010101"|"11100101"|"11110101" => return BG_15;
        when "11000001"|"11010001"|"11100001"|"11110001" => return BG_16;
        when "11101011" => return BG_17;
        when "00001000" => return BG_18;
        when "11011001" => return BG_19;
        when "11100011" => return BG_20;
        when "10000000"|"10000001"|"10000010"|"10000011"|"10000100"|"10000101"|"10000111"
                        |"10001000"|"10001001"|"10001010"|"10001011"|"10001100"|"10001101"|"10001111"
                        |"10010000"|"10010001"|"10010010"|"10010011"|"10010100"|"10010101"|"10010111"
                        |"10011000"|"10011001"|"10011010"|"10011011"|"10011100"|"10011101"|"10011111"
                        |"10100000"|"10100001"|"10100010"|"10100011"|"10100100"|"10100101"|"10100111"
                        |"10101000"|"10101001"|"10101010"|"10101011"|"10101100"|"10101101"|"10101111"
                        |"10110000"|"10110001"|"10110010"|"10110011"|"10110100"|"10110101"|"10110111"
                        |"10111000"|"10111001"|"10111010"|"10111011"|"10111100"|"10111101"|"10111111" => return BG_21;
        when "10000110"|"10001110"|"10010110"|"10011110"|"10100110"|"10101110"|"10110110"|"10111110" => return BG_22;
        when "11000110"|"11001110"|"11010110"|"11011110"|"11100110"|"11101110"|"11110110"|"11111110" => return BG_23;
        when "00000100"|"00001100"|"00010100"|"00011100"|"00100100"|"00101100"|"00111100" => return BG_24;
        when "00110100" => return BG_25;
        when "00000101"|"00001101"|"00010101"|"00011101"|"00100101"|"00101101"|"00111101" => return BG_26;
        when "00110101" => return BG_27;
        when "00100111" => return BG_28;
        when "00101111" => return BG_29;
        when "00111111" => return BG_30;
        when "00110111" => return BG_31;
        when "00000000" => return BG_32;
        when "01110110" => return BG_33;
        when "11110011" => return BG_34;
        when "11111011" => return BG_35;
        when "00001001"|"00011001"|"00101001"|"00111001" => return BG_36;
        when "00000011"|"00010011"|"00100011"|"00110011" => return BG_37;
        when "00001011"|"00011011"|"00101011"|"00111011" => return BG_38;
        when "00000111"
                               
                        |"00010111"
                              
                        |"00001111"
                               
                        |"00011111" => return BG_39;
        when "11000011" => return BG_40;
        when "11000010"|"11001010"|"11010010"|"11011010"|"11100010"|"11101010"|"11110010"|"11111010" => return BG_41;
        when "00011000" => return BG_42;
        when "00111000" => return BG_43;
        when "00110000" => return BG_44;
        when "00101000" => return BG_45;
        when "00100000" => return BG_46;
        when "11101001" => return BG_47;
        when "00010000" => return BG_48;
        when "11001101" => return BG_49;
        when "11000100"|"11001100"|"11010100"|"11011100"|"11100100"|"11101100"|"11110100"|"11111100" => return BG_50;
        when "11001001" => return BG_51;
        when "11000000"|"11001000"|"11010000"|"11011000"|"11100000"|"11101000"|"11110000"|"11111000" => return BG_52;
        when "11000111"|"11001111"|"11010111"|"11011111"|"11100111"|"11101111"|"11110111"|"11111111" => return BG_53;
        when "11011011" => return BG_54;
        when "11010011" => return BG_55;
        when "11001011" => return BG_56;
        when "11101101" => return BG_57;
        when "11011101"|"11111101" => return BG_58;
        when others => return BG_32;
        end case;
    end function;
    function Decode_CB_Group(op:std_logic_vector(7 downto 0)) return cb_group_t is
        variable opcode_bits:bit_vector(7 downto 0);
    begin
        opcode_bits:=to_bitvector(op);
        case opcode_bits is
        when "00000000"|"00000001"|"00000010"|"00000011"|"00000100"|"00000101"|"00000111"
                |"00010000"|"00010001"|"00010010"|"00010011"|"00010100"|"00010101"|"00010111"
                |"00001000"|"00001001"|"00001010"|"00001011"|"00001100"|"00001101"|"00001111"
                |"00011000"|"00011001"|"00011010"|"00011011"|"00011100"|"00011101"|"00011111"
                |"00100000"|"00100001"|"00100010"|"00100011"|"00100100"|"00100101"|"00100111"
                |"00101000"|"00101001"|"00101010"|"00101011"|"00101100"|"00101101"|"00101111"
                |"00110000"|"00110001"|"00110010"|"00110011"|"00110100"|"00110101"|"00110111"
                |"00111000"|"00111001"|"00111010"|"00111011"|"00111100"|"00111101"|"00111111" => return CG_00;
        when "00000110"|"00010110"|"00001110"|"00011110"|"00101110"|"00111110"|"00100110"|"00110110" => return CG_01;
        when "01000000"|"01000001"|"01000010"|"01000011"|"01000100"|"01000101"|"01000111"
                |"01001000"|"01001001"|"01001010"|"01001011"|"01001100"|"01001101"|"01001111"
                |"01010000"|"01010001"|"01010010"|"01010011"|"01010100"|"01010101"|"01010111"
                |"01011000"|"01011001"|"01011010"|"01011011"|"01011100"|"01011101"|"01011111"
                |"01100000"|"01100001"|"01100010"|"01100011"|"01100100"|"01100101"|"01100111"
                |"01101000"|"01101001"|"01101010"|"01101011"|"01101100"|"01101101"|"01101111"
                |"01110000"|"01110001"|"01110010"|"01110011"|"01110100"|"01110101"|"01110111"
                |"01111000"|"01111001"|"01111010"|"01111011"|"01111100"|"01111101"|"01111111" => return CG_02;
        when "01000110"|"01001110"|"01010110"|"01011110"|"01100110"|"01101110"|"01110110"|"01111110" => return CG_03;
        when "11000000"|"11000001"|"11000010"|"11000011"|"11000100"|"11000101"|"11000111"
                |"11001000"|"11001001"|"11001010"|"11001011"|"11001100"|"11001101"|"11001111"
                |"11010000"|"11010001"|"11010010"|"11010011"|"11010100"|"11010101"|"11010111"
                |"11011000"|"11011001"|"11011010"|"11011011"|"11011100"|"11011101"|"11011111"
                |"11100000"|"11100001"|"11100010"|"11100011"|"11100100"|"11100101"|"11100111"
                |"11101000"|"11101001"|"11101010"|"11101011"|"11101100"|"11101101"|"11101111"
                |"11110000"|"11110001"|"11110010"|"11110011"|"11110100"|"11110101"|"11110111"
                |"11111000"|"11111001"|"11111010"|"11111011"|"11111100"|"11111101"|"11111111" => return CG_04;
        when "11000110"|"11001110"|"11010110"|"11011110"|"11100110"|"11101110"|"11110110"|"11111110" => return CG_05;
        when "10000000"|"10000001"|"10000010"|"10000011"|"10000100"|"10000101"|"10000111"
                |"10001000"|"10001001"|"10001010"|"10001011"|"10001100"|"10001101"|"10001111"
                |"10010000"|"10010001"|"10010010"|"10010011"|"10010100"|"10010101"|"10010111"
                |"10011000"|"10011001"|"10011010"|"10011011"|"10011100"|"10011101"|"10011111"
                |"10100000"|"10100001"|"10100010"|"10100011"|"10100100"|"10100101"|"10100111"
                |"10101000"|"10101001"|"10101010"|"10101011"|"10101100"|"10101101"|"10101111"
                |"10110000"|"10110001"|"10110010"|"10110011"|"10110100"|"10110101"|"10110111"
                |"10111000"|"10111001"|"10111010"|"10111011"|"10111100"|"10111101"|"10111111" => return CG_06;
        when "10000110"|"10001110"|"10010110"|"10011110"|"10100110"|"10101110"|"10110110"|"10111110" => return CG_07;
        when others => return CG_00;
        end case;
    end function;
    function Decode_ED_Group(op:std_logic_vector(7 downto 0)) return ed_group_t is
        variable opcode_bits:bit_vector(7 downto 0);
    begin
        opcode_bits:=to_bitvector(op);
        case opcode_bits is
        when x"84"|x"8C"|x"A4"|x"AC"|"00000000"|"00000001"|"00000010"|"00000011"|"00000101"|"00000110"
                                |"00001000"|"00001001"|"00001010"|"00001011"|"00001101"|"00001110"
                                |"00010000"|"00010001"|"00010010"|"00010011"|"00010101"|"00010110"
                                |"00011000"|"00011001"|"00011010"|"00011011"|"00011101"|"00011110"
                                |"00100000"|"00100001"|"00100010"|"00100011"|"00100101"|"00100110"
                                |"00101000"|"00101001"|"00101010"|"00101011"|"00101101"|"00101110"
                                |"00110000"|"00110010"|"00110011"|"00110101"|"00110110"
                                |"00111000"|"00111001"|"00111010"|"00111011"|"00111101"


                                |"10000000"|"10000001"|"10000010"|"10000011"|"10000101"|"10000110"|"10000111"
                                |"10001000"|"10001001"|"10001010"|"10001011"|"10001101"|"10001110"|"10001111"
                                |"10010000"|"10010001"|"10010010"|"10010011"|"10010100"|"10010101"|"10010110"|"10010111"
                                |"10011000"|"10011001"|"10011010"|"10011011"|"10011100"|"10011101"|"10011110"|"10011111"
                                |"10100101"|"10100110"|"10100111"
                                |"10101101"|"10101110"|"10101111"
                                |                                            "10110100"|"10110101"|"10110110"|"10110111"
                                |                                            "10111100"|"10111101"|"10111110"|"10111111"
                                |"11000000"|           "11000010"|           "11000100"|"11000101"|"11000110"|"11000111"
                                |"11001000"|           "11001010"|"11001011"|"11001100"|"11001101"|"11001110"|"11001111"
                                |"11010000"|           "11010010"|"11010011"|"11010100"|"11010101"|"11010110"|"11010111"
                                |"11011000"|           "11011010"|"11011011"|"11011100"|"11011101"|"11011110"|"11011111"
                                |"11100000"|"11100001"|"11100010"|"11100011"|"11100100"|"11100101"|"11100110"|"11100111"
                                |"11101000"|"11101001"|"11101010"|"11101011"|"11101100"|"11101101"|"11101110"|"11101111"
                                |"11110000"|"11110001"|"11110010"|           "11110100"|"11110101"|"11110110"|"11110111"
                                |"11111000"|"11111001"|"11111010"|"11111011"|"11111100"|"11111101"|"11111110"|"11111111" => return EG_00;
        when x"07"|x"17"|x"27"|x"37"|x"31"|x"0F"|x"1F"|x"2F"|x"3F"|x"3E" => return EG_01;
        when "00000100"|"00001100"|"00010100"|"00011100"|
                             "00100100"|"00101100"|"00110100"|"00111100" => return EG_02;
        when "01111110"|"01111111" => return EG_03;
        when "01010111" => return EG_04;
        when "01011111" => return EG_05;
        when "01000111" => return EG_06;
        when "01001111" => return EG_07;
        when "01001011"|"01011011"|"01101011"|"01111011" => return EG_08;
        when "01000011"|"01010011"|"01100011"|"01110011" => return EG_09;
        when "10100000" | "10101000" | "10110000" | "10111000" => return EG_10;
        when "10100001" | "10101001" | "10110001" | "10111001" => return EG_11;
        when "01000100"|"01001100"|"01010100"|"01011100"|"01100100"|"01101100"|"01110100"|"01111100" => return EG_12;
        when "01000110"|"01001110"|"01100110"|"01101110" => return EG_13;
        when "01010110" => return EG_14;
        when "01110110" => return EG_15;
        when "01011110"|"01110111" => return EG_16;
        when "01001010"|"01011010"|"01101010"|"01111010" => return EG_17;
        when "01000010"|"01010010"|"01100010"|"01110010" => return EG_18;
        when "01101111" => return EG_19;
        when "01100111" => return EG_20;
        when "01000101"|"01001101"|"01010101"|"01011101"|"01100101"|"01101101"|"01110101"|"01111101" => return EG_21;
        when "01000000"|"01001000"|"01010000"|"01011000"|"01100000"|"01101000"|"01110000"|"01111000" => return EG_22;
        when "01000001"|"01001001"|"01010001"|"01011001"|"01100001"|"01101001"|"01110001"|"01111001" => return EG_23;
        when "10100010" | "10101010" | "10110010" | "10111010" => return EG_24;
        when "10100011" | "10101011" | "10110011" | "10111011" => return EG_25;
        when "11000001"|"11001001"|"11010001"|"11011001" => return EG_26;
        when "11000011"|"11110011" => return EG_27;
        when others => return EG_00;
        end case;
    end function;
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
        if mode_id=0 and ex='1' and pg="10" and op=x"74" then c(EC_TSTIO):='1';end if;
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
        -- Capture final-page predicates; no new pipeline cycle or raw-prefix input.
        if pg="00" then c(EC_PAGE_BASE):='1';end if;
        if pg="10" then c(EC_PAGE_ED):='1';end if;
        if op=x"31" or op=x"3E" then c(EC_IND_OPPOSITE):='1';end if;
        if op=x"03" or op=x"13" or op=x"23" or op=x"33" or op=x"54" or op=x"66" then c(EC_EA_SOURCE_IY):='1';end if;
        if op=x"32" or op=x"54" then c(EC_EA_TARGET_IX):='1';end if;
        if op=x"33" or op=x"55" then c(EC_EA_TARGET_IY):='1';end if;
        if ex='1' and pg="00" and op=x"E9" then c(EC_JP_INDIRECT):='1';end if;
        if pg="00" and op=x"31" then c(EC_SP_IMMEDIATE):='1';end if;
        if op(5 downto 4)="10" then c(EC_PAIR_HL):='1';end if;
        if op(5 downto 4)="11" then c(EC_PAIR_SP):='1';end if;
        if op(3 downto 0)="0101" then c(EC_STACK_PUSH):='1';end if;
        if op(3 downto 0)="0001" then c(EC_STACK_POP):='1';end if;
        if op=x"32" then c(EC_BYTE_STORE):='1';end if;
        if ex='1' and pg="00" and op(7 downto 6)="00" and op(3 downto 0)="0001" then c(EC_IMM_PAIR):='1';end if;
        if op=x"CB" or op=x"36" then c(EC_INDEX_FETCH):='1';end if;
        if op=x"7D" then c(EC_MADL_SET):='1';end if;
        if op=x"6D" then c(EC_MB_WRITE):='1';end if;
        if op=x"36" then c(EC_LD_MEM_IMM):='1';end if;
        if pg/="00" and op(5 downto 4)="11" then c(EC_ABS_SP):='1';end if;
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
