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
--  0211 : Fixed IM 1
--  0214 : Fixed mostly flags, only the block instructions now fail the zex regression test
--  0235 : Added IM 2 fix by Mike Johnson
--  0238 : Added NoRead signal
--  0238b: Fixed instruction timing for POP and DJNZ
--  0240 : Added (IX/IY+d) states, removed op-codes from mode 2 and added all remaining mode 3 op-codes
--  0242 : Fixed I/O instruction timing, cleanup
--  0242a: 31st of August, 2003 by Kazuhiro Tsujikawa (tujikawa@hat.hi-ho.ne.jp)
--         Fixed INI, IND, INIR, INDR, OUTI, OUTD, OTIR, OTDR instructions
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

entity T80_MCode_eZ80 is
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
                XY_State    : in std_logic_vector(1 downto 0);
                MCycles     : out std_logic_vector(2 downto 0);
                TStates     : out std_logic_vector(2 downto 0);
                Prefix      : out std_logic_vector(1 downto 0); -- None,CB,ED,DD/FD
                Inc_PC      : out std_logic;
                Inc_WZ      : out std_logic;
                IncDec_16   : out std_logic_vector(3 downto 0); -- BC,DE,HL,SP   0 is inc
                Read_To_Reg : out std_logic;
                Read_To_Acc : out std_logic;
                Set_BusA_To : out std_logic_vector(3 downto 0); -- B,C,D,E,H,L,DI/DB,A,SP(L),SP(M),0,F
                Set_BusB_To : out std_logic_vector(3 downto 0); -- B,C,D,E,H,L,DI,A,SP(L),SP(M),1,F,PC(L),PC(M),0
                ALU_Op      : out std_logic_vector(3 downto 0);
                        -- ADD, ADC, SUB, SBC, AND, XOR, OR, CP, ROT, BIT, SET, RES, DAA, RLD, RRD, None
                ALU_cpi     : out std_logic;    --for undoc XY-Flags
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
end T80_MCode_eZ80;

architecture rtl of T80_MCode_eZ80 is
        signal Legacy_Write : std_logic;

        constant aNone  : std_logic_vector(2 downto 0) := "111";
        constant aBC    : std_logic_vector(2 downto 0) := "000";
        constant aDE    : std_logic_vector(2 downto 0) := "001";
        constant aXY    : std_logic_vector(2 downto 0) := "010";
        constant aIOA   : std_logic_vector(2 downto 0) := "100";
        constant aSP    : std_logic_vector(2 downto 0) := "101";
        constant aZI    : std_logic_vector(2 downto 0) := "110";

        function is_cc_true(
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

begin

        process (Base_Group, CB_Group, ED_Group, Exec_Control, Interrupt_Long, IR, Write_Class, ISet, MCycle, F, NMICycle, IntCycle, XY_State, Ext_Active, Data_Long, Stream_Long, ADL_Mode, Has_Width, Interrupt_Mode, Branch_Condition)
                variable DDD : std_logic_vector(2 downto 0);
                variable SSS : std_logic_vector(2 downto 0);
                variable Tst_Active, Indexed_Pair_Active, Block_IO2 : boolean;
                variable DPair : std_logic_vector(1 downto 0);
                variable lastaddr, countdata, cycle : integer;
                variable pairnum : std_logic_vector(1 downto 0);
                variable reading : boolean;
                variable IRB : bit_vector(7 downto 0);
        begin
                DDD := IR(5 downto 3);
                SSS := IR(2 downto 0);
                DPair := IR(5 downto 4);
                IRB := to_bitvector(IR);
                Block_IO2:=Exec_Control(EC_IO2)='1' and IntCycle='0' and NMICycle='0';
                Tst_Active:=Exec_Control(EC_TST)='1' and IntCycle='0' and NMICycle='0';
                Indexed_Pair_Active:=Exec_Control(EC_PAIR_INDEX)='1' and IntCycle='0' and NMICycle='0';
                Flow_Cond <= Branch_Condition;
                MCycles <= "001";
                if MCycle = "001" then
                        TStates <= "100";
                else
                        TStates <= "011";
                end if;
                Prefix <= "00";
                Inc_PC <= '0';
                Inc_WZ <= '0';
                IncDec_16 <= "0000";
                Read_To_Acc <= '0';
                Read_To_Reg <= '0';
                Set_BusB_To <= "0000";
                Set_BusA_To <= "0000";
                ALU_Op <= "0" & IR(5 downto 3);
                ALU_cpi <= '0';
                Save_ALU <= '0';
                PreserveC <= '0';
                Arith16 <= '0';
                IORQ <= '0';
                Set_Addr_To <= aNone;
                Jump <= '0';
                JumpE <= '0';
                JumpXY <= '0';
                Call <= '0';
                RstP <= '0';
                LDZ <= '0';
                LDW <= '0';
                LDSPHL <= '0';
                Special_LD <= "000";
                ExchangeDH <= '0';
                ExchangeRp <= '0';
                ExchangeAF <= '0';
                ExchangeRS <= '0';
                I_DJNZ <= '0';
                I_CPL <= '0';
                I_CCF <= '0';
                I_SCF <= '0';
                I_RETN <= '0';
                I_BT <= '0';
                I_BC <= '0';
                I_BTR <= '0';
                I_RLD <= '0';
                I_RRD <= '0';
                I_INRC <= '0';
                SetDI <= '0';
                SetEI <= '0';
                IMode <= "11";
                Halt <= '0';
                NoRead <= '0';
                Legacy_Write <= '0';
                XYbit_undoc <= '0';

                case ISet is
                when "00" =>
                    -- R17: indexed pair memory is a decode branch, before legacy rotates/LDs.
                    if Indexed_Pair_Active then
                        if Data_Long='1' then MCycles<="101";else MCycles<="100";end if;
                        if MCycle="010" then Inc_PC<='1';TStates<="100";end if;
                        if Write_Class(7 downto 4)=x"B" then
                            if MCycle="011" then Read_To_Reg<='1';Set_BusA_To<="0101";
                            elsif MCycle="100" then Read_To_Reg<='1';Set_BusA_To<="0100";end if;
                        end if;
                    else


------------------------------------------------------------------------------
--
--      Unprefixed instructions
--
------------------------------------------------------------------------------

                case to_integer(unsigned(Base_Group)) is
-- 8 BIT LOAD GROUP
                when 0 => -- BG_00
                        -- LD r,r'
                        Set_BusB_To(2 downto 0) <= SSS;
                        ExchangeRp <= '1';
                        Set_BusA_To(2 downto 0) <= DDD;
                        Read_To_Reg <= '1';
                when 1 => -- BG_01
                        -- LD r,n
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                Inc_PC <= '1';
                                Set_BusA_To(2 downto 0) <= DDD;
                                Read_To_Reg <= '1';
                        when others => null;
                        end case;
                when 2 => -- BG_02
                        -- LD r,(HL)
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aXY;
                        when 2 =>
                                Set_BusA_To(2 downto 0) <= DDD;
                                Read_To_Reg <= '1';
                        when others => null;
                        end case;
                when 3 => -- BG_03
                        -- LD (HL),r
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aXY;
                                Set_BusB_To(2 downto 0) <= SSS;
                                Set_BusB_To(3) <= '0';
                        when 2 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 4 => -- BG_04
                        -- LD (HL),n
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                Inc_PC <= '1';
                                Set_Addr_To <= aXY;
                                Set_BusB_To(2 downto 0) <= SSS;
                                Set_BusB_To(3) <= '0';
                        when 3 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 5 => -- BG_05
                        -- LD A,(BC)
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aBC;
                        when 2 =>
                                Read_To_Acc <= '1';
                        when others => null;
                        end case;
                when 6 => -- BG_06
                        -- LD A,(DE)
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aDE;
                        when 2 =>
                                Read_To_Acc <= '1';
                        when others => null;
                        end case;
                when 7 => -- BG_07
                        if Mode = 3 then
                                -- LDD A,(HL)
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                when 2 =>
                                        Read_To_Acc <= '1';
                                        IncDec_16 <= "1110";
                                when others => null;
                                end case;
                        else
                                -- LD A,(nn)
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                when 4 =>
                                        Read_To_Acc <= '1';
                                when others => null;
                                end case;
                        end if;
                when 8 => -- BG_08
                        -- LD (BC),A
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aBC;
                                Set_BusB_To <= "0111";
                        when 2 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 9 => -- BG_09
                        -- LD (DE),A
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aDE;
                                Set_BusB_To <= "0111";
                        when 2 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 10 => -- BG_10
                        if Mode = 3 then
                                -- LDD (HL),A
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                        Set_BusB_To <= "0111";
                                when 2 =>
                                        Legacy_Write <= '1';
                                        IncDec_16 <= "1110";
                                when others => null;
                                end case;
                        else
                                -- LD (nn),A
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        Set_BusB_To <= "0111";
                                when 4 =>
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        end if;

-- 16 BIT LOAD GROUP
                when 11 => -- BG_11
                        -- LD dd,nn
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                Inc_PC <= '1';
                                Read_To_Reg <= '1';
                                if DPAIR = "11" then
                                        Set_BusA_To(3 downto 0) <= "1000";
                                else
                                        Set_BusA_To(2 downto 1) <= DPAIR;
                                        Set_BusA_To(0) <= '1';
                                end if;
                        when 3 =>
                                Inc_PC <= '1';
                                Read_To_Reg <= '1';
                                if DPAIR = "11" then
                                        Set_BusA_To(3 downto 0) <= "1001";
                                else
                                        Set_BusA_To(2 downto 1) <= DPAIR;
                                        Set_BusA_To(0) <= '0';
                                end if;
                        when others => null;
                        end case;
                when 12 => -- BG_12
                        if Mode = 3 then
                                -- LDI A,(HL)
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                when 2 =>
                                        Read_To_Acc <= '1';
                                        IncDec_16 <= "0110";
                                when others => null;
                                end case;
                        else
                                -- LD HL,(nn)
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                when 4 =>
                                        Set_BusA_To(2 downto 0) <= "101"; -- L
                                        Read_To_Reg <= '1';
                                        Inc_WZ <= '1';
                                        Set_Addr_To <= aZI;
                                when 5 =>
                                        Set_BusA_To(2 downto 0) <= "100"; -- H
                                        Read_To_Reg <= '1';
                                when others => null;
                                end case;
                        end if;
                when 13 => -- BG_13
                        if Mode = 3 then
                                -- LDI (HL),A
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                        Set_BusB_To <= "0111";
                                when 2 =>
                                        Legacy_Write <= '1';
                                        IncDec_16 <= "0110";
                                when others => null;
                                end case;
                        else
                                -- LD (nn),HL
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                        Set_BusB_To <= "0101"; -- L
                                when 4 =>
                                        Inc_WZ <= '1';
                                        Set_Addr_To <= aZI;
                                        Legacy_Write <= '1';
                                        Set_BusB_To <= "0100"; -- H
                                when 5 =>
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        end if;
                when 14 => -- BG_14
                        -- LD SP,HL
                        TStates <= "110";
                        LDSPHL <= '1';
                when 15 => -- BG_15
                        -- PUSH qq
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                TStates <= "101";
                                IncDec_16 <= "1111";
                                Set_Addr_TO <= aSP;
                                if DPAIR = "11" then
                                        Set_BusB_To <= "0111";
                                else
                                        Set_BusB_To(2 downto 1) <= DPAIR;
                                        Set_BusB_To(0) <= '0';
                                        Set_BusB_To(3) <= '0';
                                end if;
                        when 2 =>
                                IncDec_16 <= "1111";
                                Set_Addr_To <= aSP;
                                if DPAIR = "11" then
                                        Set_BusB_To <= "1011";
                                else
                                        Set_BusB_To(2 downto 1) <= DPAIR;
                                        Set_BusB_To(0) <= '1';
                                        Set_BusB_To(3) <= '0';
                                end if;
                                Legacy_Write <= '1';
                        when 3 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 16 => -- BG_16
                        -- POP qq
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aSP;
                        when 2 =>
                                IncDec_16 <= "0111";
                                Set_Addr_To <= aSP;
                                Read_To_Reg <= '1';
                                if DPAIR = "11" then
                                        Set_BusA_To(3 downto 0) <= "1011";
                                else
                                        Set_BusA_To(2 downto 1) <= DPAIR;
                                        Set_BusA_To(0) <= '1';
                                end if;
                        when 3 =>
                                IncDec_16 <= "0111";
                                Read_To_Reg <= '1';
                                if DPAIR = "11" then
                                        Set_BusA_To(3 downto 0) <= "0111";
                                else
                                        Set_BusA_To(2 downto 1) <= DPAIR;
                                        Set_BusA_To(0) <= '0';
                                end if;
                        when others => null;
                        end case;

-- EXCHANGE, BLOCK TRANSFER AND SEARCH GROUP
                when 17 => -- BG_17
                        if Mode /= 3 then
                                -- EX DE,HL
                                ExchangeDH <= '1';
                        end if;
                when 18 => -- BG_18
                        if Mode = 3 then
                                -- LD (nn),SP
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                        Set_BusB_To <= "1000";
                                when 4 =>
                                        Inc_WZ <= '1';
                                        Set_Addr_To <= aZI;
                                        Legacy_Write <= '1';
                                        Set_BusB_To <= "1001";
                                when 5 =>
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        elsif Mode < 2 then
                                -- EX AF,AF'
                                ExchangeAF <= '1';
                        end if;
                when 19 => -- BG_19
                        if Mode = 3 then
                                -- RETI
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_TO <= aSP;
                                when 2 =>
                                        IncDec_16 <= "0111";
                                        Set_Addr_To <= aSP;
                                        LDZ <= '1';
                                when 3 =>
                                        Jump <= '1';
                                        IncDec_16 <= "0111";
                                        I_RETN <= '1';
                                        SetEI <= '1';
                                when others => null;
                                end case;
                        elsif Mode < 2 then
                                -- EXX
                                ExchangeRS <= '1';
                        end if;
                when 20 => -- BG_20
                        if Mode /= 3 then
                                -- EX (SP),HL
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aSP;
                                when 2 =>
                                        Read_To_Reg <= '1';
                                        Set_BusA_To <= "0101";
                                        Set_BusB_To <= "0101";
                                        Set_Addr_To <= aSP;
                                when 3 =>
                                        IncDec_16 <= "0111";
                                        Set_Addr_To <= aSP;
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                when 4 =>
                                        Read_To_Reg <= '1';
                                        Set_BusA_To <= "0100";
                                        Set_BusB_To <= "0100";
                                        Set_Addr_To <= aSP;
                                when 5 =>
                                        IncDec_16 <= "1111";
                                        TStates <= "101";
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        end if;

-- 8 BIT ARITHMETIC AND LOGICAL GROUP
                when 21 => -- BG_21
                        -- ADD A,r
                        -- ADC A,r
                        -- SUB A,r
                        -- SBC A,r
                        -- AND A,r
                        -- OR A,r
                        -- XOR A,r
                        -- CP A,r
                        Set_BusB_To(2 downto 0) <= SSS;
                        Set_BusA_To(2 downto 0) <= "111";
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                when 22 => -- BG_22
                        -- ADD A,(HL)
                        -- ADC A,(HL)
                        -- SUB A,(HL)
                        -- SBC A,(HL)
                        -- AND A,(HL)
                        -- OR A,(HL)
                        -- XOR A,(HL)
                        -- CP A,(HL)
                        MCycles <= "010";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aXY;
                        when 2 =>
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                Set_BusB_To(2 downto 0) <= SSS;
                                Set_BusA_To(2 downto 0) <= "111";
                        when others => null;
                        end case;
                when 23 => -- BG_23
                        -- ADD A,n
                        -- ADC A,n
                        -- SUB A,n
                        -- SBC A,n
                        -- AND A,n
                        -- OR A,n
                        -- XOR A,n
                        -- CP A,n
                        MCycles <= "010";
                        if MCycle = "010" then
                                Inc_PC <= '1';
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                Set_BusB_To(2 downto 0) <= SSS;
                                Set_BusA_To(2 downto 0) <= "111";
                        end if;
                when 24 => -- BG_24
                        -- INC r
                        Set_BusB_To <= "1010";
                        Set_BusA_To(2 downto 0) <= DDD;
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                        PreserveC <= '1';
                        ALU_Op <= "0000";
                when 25 => -- BG_25
                        -- INC (HL)
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aXY;
                        when 2 =>
                                TStates <= "100";
                                Set_Addr_To <= aXY;
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                PreserveC <= '1';
                                ALU_Op <= "0000";
                                Set_BusB_To <= "1010";
                                Set_BusA_To(2 downto 0) <= DDD;
                        when 3 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;
                when 26 => -- BG_26
                        -- DEC r
                        Set_BusB_To <= "1010";
                        Set_BusA_To(2 downto 0) <= DDD;
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                        PreserveC <= '1';
                        ALU_Op <= "0010";
                when 27 => -- BG_27
                        -- DEC (HL)
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                Set_Addr_To <= aXY;
                        when 2 =>
                                TStates <= "100";
                                Set_Addr_To <= aXY;
                                ALU_Op <= "0010";
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                PreserveC <= '1';
                                Set_BusB_To <= "1010";
                                Set_BusA_To(2 downto 0) <= DDD;
                        when 3 =>
                                Legacy_Write <= '1';
                        when others => null;
                        end case;

-- GENERAL PURPOSE ARITHMETIC AND CPU CONTROL GROUPS
                when 28 => -- BG_28
                        -- DAA
                        Set_BusA_To(2 downto 0) <= "111";
                        Read_To_Reg <= '1';
                        ALU_Op <= "1100";
                        Save_ALU <= '1';
                when 29 => -- BG_29
                        -- CPL
                        I_CPL <= '1';
                when 30 => -- BG_30
                        -- CCF
                        I_CCF <= '1';
                when 31 => -- BG_31
                        -- SCF
                        I_SCF <= '1';
                when 32 => -- BG_32
                        if NMICycle = '1' then
                                -- NMI
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        TStates <= "101";
                                        IncDec_16 <= "1111";
                                        Set_Addr_To <= aSP;
                                        Set_BusB_To <= "1101";
                                when 2 =>
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                        IncDec_16 <= "1111";
                                        Set_Addr_To <= aSP;
                                        Set_BusB_To <= "1100";
                                when 3 =>
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        elsif IntCycle = '1' then
                                -- INT (IM 2)
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        LDZ <= '1';
                                        TStates <= "101";
                                        IncDec_16 <= "1111";
                                        Set_Addr_To <= aSP;
                                        Set_BusB_To <= "1101";
                                when 2 =>
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                        IncDec_16 <= "1111";
                                        Set_Addr_To <= aSP;
                                        Set_BusB_To <= "1100";
                                when 3 =>
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                when 4 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 5 =>
                                        Jump <= '1';
                                when others => null;
                                end case;
                        else
                                -- NOP
                        end if;
                when 33 => -- BG_33
                        -- HALT
                        Halt <= '1';
                when 34 => -- BG_34
                        -- DI
                        SetDI <= '1';
                when 35 => -- BG_35
                        -- EI
                        SetEI <= '1';

-- 16 BIT ARITHMETIC GROUP
                when 36 => -- BG_36
                        -- ADD HL,ss
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                NoRead <= '1';
                                ALU_Op <= "0000";
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                Set_BusA_To(2 downto 0) <= "101";
                                case to_integer(unsigned(IR(5 downto 4))) is
                                when 0|1|2 =>
                                        Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                        Set_BusB_To(0) <= '1';
                                when others =>
                                        Set_BusB_To <= "1000";
                                end case;
                                TStates <= "100";
                                Arith16 <= '1';
                        when 3 =>
                                NoRead <= '1';
                                Read_To_Reg <= '1';
                                Save_ALU <= '1';
                                ALU_Op <= "0001";
                                Set_BusA_To(2 downto 0) <= "100";
                                case to_integer(unsigned(IR(5 downto 4))) is
                                when 0|1|2 =>
                                        Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                when others =>
                                        Set_BusB_To <= "1001";
                                end case;
                                Arith16 <= '1';
                        when others =>
                        end case;
                when 37 => -- BG_37
                        -- INC ss
                        TStates <= "110";
                        IncDec_16(3 downto 2) <= "01";
                        IncDec_16(1 downto 0) <= DPair;
                when 38 => -- BG_38
                        -- DEC ss
                        TStates <= "110";
                        IncDec_16(3 downto 2) <= "11";
                        IncDec_16(1 downto 0) <= DPair;

-- ROTATE AND SHIFT GROUP
                when 39 => -- BG_39
                        -- RRA
                        Set_BusA_To(2 downto 0) <= "111";
                        ALU_Op <= "1000";
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';

-- JUMP GROUP
                when 40 => -- BG_40
                        -- JP nn
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                Inc_PC <= '1';
                                LDZ <= '1';
                        when 3 =>
                                Inc_PC <= '1';
                                Jump <= '1';
                        when others => null;
                        end case;
                when 41 => -- BG_41
                        if IR(5) = '1' and Mode = 3 then
                                case IRB(4 downto 3) is
                                when "00" =>
                                        -- LD ($FF00+C),A
                                        MCycles <= "010";
                                        case to_integer(unsigned(MCycle)) is
                                        when 1 =>
                                                Set_Addr_To <= aBC;
                                                Set_BusB_To     <= "0111";
                                        when 2 =>
                                                Legacy_Write <= '1';
                                                IORQ <= '1';
                                        when others =>
                                        end case;
                                when "01" =>
                                        -- LD (nn),A
                                        MCycles <= "100";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                Inc_PC <= '1';
                                                LDZ <= '1';
                                        when 3 =>
                                                Set_Addr_To <= aZI;
                                                Inc_PC <= '1';
                                                Set_BusB_To <= "0111";
                                        when 4 =>
                                                Legacy_Write <= '1';
                                        when others => null;
                                        end case;
                                when "10" =>
                                        -- LD A,($FF00+C)
                                        MCycles <= "010";
                                        case to_integer(unsigned(MCycle)) is
                                        when 1 =>
                                                Set_Addr_To <= aBC;
                                        when 2 =>
                                                Read_To_Acc <= '1';
                                                IORQ <= '1';
                                        when others =>
                                        end case;
                                when "11" =>
                                        -- LD A,(nn)
                                        MCycles <= "100";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                Inc_PC <= '1';
                                                LDZ <= '1';
                                        when 3 =>
                                                Set_Addr_To <= aZI;
                                                Inc_PC <= '1';
                                        when 4 =>
                                                Read_To_Acc <= '1';
                                        when others => null;
                                        end case;
                                end case;
                        else
                                -- JP cc,nn
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Inc_PC <= '1';
                                        if Branch_Condition='1' then
                                                Jump <= '1';
                                        end if;
                                when others => null;
                                end case;
                        end if;
                when 42 => -- BG_42
                        if Mode /= 2 then
                                -- JR e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;
                when 43 => -- BG_43
                        if Mode /= 2 then
                                -- JR C,e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        if F(Flag_C) = '0' then
                                                MCycles <= "010";
                                        end if;
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;
                when 44 => -- BG_44
                        if Mode /= 2 then
                                -- JR NC,e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        if F(Flag_C) = '1' then
                                                MCycles <= "010";
                                        end if;
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;
                when 45 => -- BG_45
                        if Mode /= 2 then
                                -- JR Z,e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        if F(Flag_Z) = '0' then
                                                MCycles <= "010";
                                        end if;
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;
                when 46 => -- BG_46
                        if Mode /= 2 then
                                -- JR NZ,e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        if F(Flag_Z) = '1' then
                                                MCycles <= "010";
                                        end if;
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;
                when 47 => -- BG_47
                        -- JP (HL)
                        JumpXY <= '1';
                when 48 => -- BG_48
                        if Mode = 3 then
                                I_DJNZ <= '1';
                        elsif Mode < 2 then
                                -- DJNZ,e
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        TStates <= "101";
                                        I_DJNZ <= '1';
                                        Set_BusB_To <= "1010";
                                        Set_BusA_To(2 downto 0) <= "000";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        ALU_Op <= "0010";
                                when 2 =>
                                        I_DJNZ <= '1';
                                        Inc_PC <= '1';
                                when 3 =>
                                        NoRead <= '1';
                                        JumpE <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        end if;

-- CALL AND RETURN GROUP
                when 49 => -- BG_49
                        -- CALL nn
                        MCycles <= "101";
                        case to_integer(unsigned(MCycle)) is
                        when 2 =>
                                Inc_PC <= '1';
                                LDZ <= '1';
                        when 3 =>
                                IncDec_16 <= "1111";
                                Inc_PC <= '1';
                                TStates <= "100";
                                Set_Addr_To <= aSP;
                                LDW <= '1';
                                Set_BusB_To <= "1101";
                        when 4 =>
                                Legacy_Write <= '1';
                                IncDec_16 <= "1111";
                                Set_Addr_To <= aSP;
                                Set_BusB_To <= "1100";
                        when 5 =>
                                Legacy_Write <= '1';
                                Call <= '1';
                        when others => null;
                        end case;
                when 50 => -- BG_50
                        if IR(5) = '0' or Mode /= 3 then
                                -- CALL cc,nn
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                        if Branch_Condition='1' then
                                                IncDec_16 <= "1111";
                                                Set_Addr_TO <= aSP;
                                                TStates <= "100";
                                                Set_BusB_To <= "1101";
                                        else
                                                MCycles <= "011";
                                        end if;
                                when 4 =>
                                        Legacy_Write <= '1';
                                        IncDec_16 <= "1111";
                                        Set_Addr_To <= aSP;
                                        Set_BusB_To <= "1100";
                                when 5 =>
                                        Legacy_Write <= '1';
                                        Call <= '1';
                                when others => null;
                                end case;
                        end if;
                when 51 => -- BG_51
                        -- RET
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                TStates <= "101";
                                Set_Addr_TO <= aSP;
                        when 2 =>
                                IncDec_16 <= "0111";
                                Set_Addr_To <= aSP;
                                LDZ <= '1';
                        when 3 =>
                                Jump <= '1';
                                IncDec_16 <= "0111";
                        when others => null;
                        end case;
                when 52 => -- BG_52
                        if IR(5) = '1' and Mode = 3 then
                                case IRB(4 downto 3) is
                                when "00" =>
                                        -- LD ($FF00+nn),A
                                        MCycles <= "011";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                Inc_PC <= '1';
                                                Set_Addr_To <= aIOA;
                                                Set_BusB_To     <= "0111";
                                        when 3 =>
                                                Legacy_Write <= '1';
                                        when others => null;
                                        end case;
                                when "01" =>
                                        -- ADD SP,n
                                        MCycles <= "011";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                ALU_Op <= "0000";
                                                Inc_PC <= '1';
                                                Read_To_Reg <= '1';
                                                Save_ALU <= '1';
                                                Set_BusA_To <= "1000";
                                                Set_BusB_To <= "0110";
                                        when 3 =>
                                                NoRead <= '1';
                                                Read_To_Reg <= '1';
                                                Save_ALU <= '1';
                                                ALU_Op <= "0001";
                                                Set_BusA_To <= "1001";
                                                Set_BusB_To <= "1110";  -- Incorrect unsigned !!!!!!!!!!!!!!!!!!!!!
                                        when others =>
                                        end case;
                                when "10" =>
                                        -- LD A,($FF00+nn)
                                        MCycles <= "011";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                Inc_PC <= '1';
                                                Set_Addr_To <= aIOA;
                                        when 3 =>
                                                Read_To_Acc <= '1';
                                        when others => null;
                                        end case;
                                when "11" =>
                                        -- LD HL,SP+n   -- Not correct !!!!!!!!!!!!!!!!!!!
                                        MCycles <= "101";
                                        case to_integer(unsigned(MCycle)) is
                                        when 2 =>
                                                Inc_PC <= '1';
                                                LDZ <= '1';
                                        when 3 =>
                                                Set_Addr_To <= aZI;
                                                Inc_PC <= '1';
                                                LDW <= '1';
                                        when 4 =>
                                                Set_BusA_To(2 downto 0) <= "101"; -- L
                                                Read_To_Reg <= '1';
                                                Inc_WZ <= '1';
                                                Set_Addr_To <= aZI;
                                        when 5 =>
                                                Set_BusA_To(2 downto 0) <= "100"; -- H
                                                Read_To_Reg <= '1';
                                        when others => null;
                                        end case;
                                end case;
                        else
                                -- RET cc
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        if Branch_Condition='1' then
                                                Set_Addr_TO <= aSP;
                                        else
                                                MCycles <= "001";
                                        end if;
                                        TStates <= "101";
                                when 2 =>
                                        IncDec_16 <= "0111";
                                        Set_Addr_To <= aSP;
                                        LDZ <= '1';
                                when 3 =>
                                        Jump <= '1';
                                        IncDec_16 <= "0111";
                                when others => null;
                                end case;
                        end if;
                when 53 => -- BG_53
                        -- RST p
                        MCycles <= "011";
                        case to_integer(unsigned(MCycle)) is
                        when 1 =>
                                TStates <= "101";
                                IncDec_16 <= "1111";
                                Set_Addr_To <= aSP;
                                Set_BusB_To <= "1101";
                        when 2 =>
                                Legacy_Write <= '1';
                                IncDec_16 <= "1111";
                                Set_Addr_To <= aSP;
                                Set_BusB_To <= "1100";
                        when 3 =>
                                Legacy_Write <= '1';
                                RstP <= '1';
                        when others => null;
                        end case;

-- INPUT AND OUTPUT GROUP
                when 54 => -- BG_54
                        if Mode /= 3 then
                                -- IN A,(n)
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        Set_Addr_To <= aIOA;
                                when 3 =>
                                        Read_To_Acc <= '1';
                                        IORQ <= '1';
                                when others => null;
                                end case;
                        end if;
                when 55 => -- BG_55
                        if Mode /= 3 then
                                -- OUT (n),A
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        Set_Addr_To <= aIOA;
                                        Set_BusB_To     <= "0111";
                                when 3 =>
                                        Legacy_Write <= '1';
                                        IORQ <= '1';
                                when others => null;
                                end case;
                        end if;

------------------------------------------------------------------------------
------------------------------------------------------------------------------
-- MULTIBYTE INSTRUCTIONS
------------------------------------------------------------------------------
------------------------------------------------------------------------------

                when 56 => -- BG_56
                        if Mode /= 2 then
                                Prefix <= "01";
                        end if;

                when 57 => -- BG_57
                        if Mode < 2 then
                                Prefix <= "10";
                        end if;

                when 58 => -- BG_58
                        if Mode < 2 then
                                Prefix <= "11";
                        end if;

                when others => null;
                end case;
                    end if; -- R17 indexed/legacy base decode

                when "01" =>

------------------------------------------------------------------------------
--
--      CB prefixed instructions
--
------------------------------------------------------------------------------

            Set_BusA_To(2 downto 0) <= IR(2 downto 0);
            Set_BusB_To(2 downto 0) <= IR(2 downto 0);

            case to_integer(unsigned(CB_Group)) is
            when 0 => -- CG_00
                -- RLC r
                -- RL r
                -- RRC r
                -- RR r
                -- SLA r
                -- SRA r
                -- SRL r
                -- SLL r (Undocumented) / SWAP r
                if XY_State="00" then
                    if MCycle = "001" then
                      ALU_Op <= "1000";
                      Read_To_Reg <= '1';
                      Save_ALU <= '1';
                    end if;
                else
                -- R/S (IX+d),Reg, undocumented
                    MCycles <= "011";
                    XYbit_undoc <= '1';
                    case to_integer(unsigned(MCycle)) is
                    when 1 | 7=>
                        Set_Addr_To <= aXY;
                    when 2 =>
                        ALU_Op <= "1000";
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                        Set_Addr_To <= aXY;
                        TStates <= "100";
                    when 3 =>
                        Legacy_Write <= '1';
                    when others => null;
                    end case;
                end if;


            when 1 => -- CG_01
                -- RLC (HL)
                -- RL (HL)
                -- RRC (HL)
                -- RR (HL)
                -- SRA (HL)
                -- SRL (HL)
                -- SLA (HL)
                -- SLL (HL) (Undocumented) / SWAP (HL)
                MCycles <= "011";
                case to_integer(unsigned(MCycle)) is
                when 1 | 7 =>
                    Set_Addr_To <= aXY;
                when 2 =>
                    ALU_Op <= "1000";
                    Read_To_Reg <= '1';
                    Save_ALU <= '1';
                    Set_Addr_To <= aXY;
                    TStates <= "100";
                when 3 =>
                    Legacy_Write <= '1';
                when others =>
                end case;
            when 2 => -- CG_02
                -- BIT b,r
                if XY_State="00" then
                    if MCycle = "001" then
                      Set_BusB_To(2 downto 0) <= IR(2 downto 0);
                      ALU_Op <= "1001";
                    end if;
                else
                -- BIT b,(IX+d), undocumented
                    MCycles <= "010";
                    XYbit_undoc <= '1';
                    case to_integer(unsigned(MCycle)) is
                    when 1 | 7=>
                        Set_Addr_To <= aXY;
                    when 2 =>
                        ALU_Op <= "1001";
                        TStates <= "100";
                    when others => null;
                    end case;
                end if;
            when 3 => -- CG_03
                -- BIT b,(HL)
                MCycles <= "010";
                case to_integer(unsigned(MCycle)) is
                when 1 | 7=>
                    Set_Addr_To <= aXY;
                when 2 =>
                    ALU_Op <= "1001";
                    TStates <= "100";
                when others => null;
                end case;
            when 4 => -- CG_04
                -- SET b,r
                if XY_State="00" then
                    if MCycle = "001" then
                      ALU_Op <= "1010";
                      Read_To_Reg <= '1';
                      Save_ALU <= '1';
                    end if;
                else
                -- SET b,(IX+d),Reg, undocumented
                    MCycles <= "011";
                    XYbit_undoc <= '1';
                    case to_integer(unsigned(MCycle)) is
                    when 1 | 7=>
                        Set_Addr_To <= aXY;
                    when 2 =>
                        ALU_Op <= "1010";
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                        Set_Addr_To <= aXY;
                        TStates <= "100";
                    when 3 =>
                        Legacy_Write <= '1';
                    when others => null;
                    end case;
                end if;
            when 5 => -- CG_05
                -- SET b,(HL)
                MCycles <= "011";
                case to_integer(unsigned(MCycle)) is
                when 1 | 7=>
                    Set_Addr_To <= aXY;
                when 2 =>
                    ALU_Op <= "1010";
                    Read_To_Reg <= '1';
                    Save_ALU <= '1';
                    Set_Addr_To <= aXY;
                    TStates <= "100";
                when 3 =>
                    Legacy_Write <= '1';
                when others => null;
                end case;
            when 6 => -- CG_06
                -- RES b,r
                if XY_State="00" then
                    if MCycle = "001" then
                      ALU_Op <= "1011";
                      Read_To_Reg <= '1';
                      Save_ALU <= '1';
                    end if;
                else
                -- RES b,(IX+d),Reg, undocumented
                    MCycles <= "011";
                    XYbit_undoc <= '1';
                    case to_integer(unsigned(MCycle)) is
                    when 1 | 7=>
                        Set_Addr_To <= aXY;
                    when 2 =>
                        ALU_Op <= "1011";
                        Read_To_Reg <= '1';
                        Save_ALU <= '1';
                        Set_Addr_To <= aXY;
                        TStates <= "100";
                    when 3 =>
                        Legacy_Write <= '1';
                    when others => null;
                    end case;
                end if;

            when 7 => -- CG_07
                -- RES b,(HL)
                MCycles <= "011";
                case to_integer(unsigned(MCycle)) is
                when 1 | 7 =>
                    Set_Addr_To <= aXY;
                when 2 =>
                    ALU_Op <= "1011";
                    Read_To_Reg <= '1';
                    Save_ALU <= '1';
                    Set_Addr_To <= aXY;
                    TStates <= "100";
                when 3 =>
                    Legacy_Write <= '1';
                when others => null;
                end case;
            when others => null;
                end case;

        when others =>

------------------------------------------------------------------------------
--
--      ED prefixed instructions
--
------------------------------------------------------------------------------

                        case to_integer(unsigned(ED_Group)) is
                        when 0 => -- EG_00
                                null; -- NOP, undocumented
                        -- R16: pair-indirect transfers share the core's EX(SP) work registers.
                        when 1 => -- EG_01
                            if Exec_Control(EC_PAIR_IND)='1' and IntCycle='0' and NMICycle='0' then
                                if Data_Long='1' then MCycles<="100";else MCycles<="011";end if;
                                if MCycle="001" then TStates<="100";else TStates<="011";end if;
                                if (IR=x"07" or IR=x"17" or IR=x"27" or IR=x"37" or IR=x"31") then
                                    if MCycle="010" then Read_To_Reg<='1';Set_BusA_To<="0101";
                                    elsif MCycle="011" then Read_To_Reg<='1';Set_BusA_To<="0100";end if;
                                end if;
                            end if;
                        when 2 => -- EG_02
                                -- R15.3: TST is an ED decode row, not a global override.
                                -- Disabled extensions retain the old undocumented NOPs.
                                if Tst_Active then
                                    ALU_Op<="0100";Set_BusA_To<="0111";
                                    Set_BusB_To<="0" & IR(5 downto 3);
                                    if IR=x"34" then
                                        MCycles<="010";Set_BusB_To<="0110";
                                        if MCycle="001" then Set_Addr_To<=aXY;end if;
                                        if MCycle="010" then Save_ALU<='1';end if;
                                    elsif MCycle="001" then Save_ALU<='1';end if;
                                end if;
                        when 3 => -- EG_03
                                -- NOP, undocumented
                                null;
-- 8 BIT LOAD GROUP
                        when 4 => -- EG_04
                                -- LD A,I
                                Special_LD <= "100";
                                TStates <= "101";
                        when 5 => -- EG_05
                                -- LD A,R
                                Special_LD <= "101";
                                TStates <= "101";
                        when 6 => -- EG_06
                                -- LD I,A
                                Special_LD <= "110";
                                TStates <= "101";
                        when 7 => -- EG_07
                                -- LD R,A
                                Special_LD <= "111";
                                TStates <= "101";
-- 16 BIT LOAD GROUP
                        when 8 => -- EG_08
                                -- LD dd,(nn)
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                when 4 =>
                                        Read_To_Reg <= '1';
                                        if IR(5 downto 4) = "11" then
                                                Set_BusA_To <= "1000";
                                        else
                                                Set_BusA_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusA_To(0) <= '1';
                                        end if;
                                        Inc_WZ <= '1';
                                        Set_Addr_To <= aZI;
                                when 5 =>
                                        Read_To_Reg <= '1';
                                        if IR(5 downto 4) = "11" then
                                                Set_BusA_To <= "1001";
                                        else
                                                Set_BusA_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusA_To(0) <= '0';
                                        end if;
                                when others => null;
                                end case;
                        when 9 => -- EG_09
                                -- LD (nn),dd
                                MCycles <= "101";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Inc_PC <= '1';
                                        LDZ <= '1';
                                when 3 =>
                                        Set_Addr_To <= aZI;
                                        Inc_PC <= '1';
                                        LDW <= '1';
                                        if IR(5 downto 4) = "11" then
                                                Set_BusB_To <= "1000";
                                        else
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusB_To(0) <= '1';
                                                Set_BusB_To(3) <= '0';
                                        end if;
                                when 4 =>
                                        Inc_WZ <= '1';
                                        Set_Addr_To <= aZI;
                                        Legacy_Write <= '1';
                                        if IR(5 downto 4) = "11" then
                                                Set_BusB_To <= "1001";
                                        else
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusB_To(0) <= '0';
                                                Set_BusB_To(3) <= '0';
                                        end if;
                                when 5 =>
                                        Legacy_Write <= '1';
                                when others => null;
                                end case;
                        when 10 => -- EG_10
                                -- LDI, LDD, LDIR, LDDR
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                        IncDec_16 <= "1100"; -- BC
                                when 2 =>
                                        Set_BusB_To <= "0110";
                                        Set_BusA_To(2 downto 0) <= "111";
                                        ALU_Op <= "0000";
                                        Set_Addr_To <= aDE;
                                        if IR(3) = '0' then
                                                IncDec_16 <= "0110"; -- IX
                                        else
                                                IncDec_16 <= "1110";
                                        end if;
                                when 3 =>
                                        I_BT <= '1';
                                        TStates <= "101";
                                        Legacy_Write <= '1';
                                        if IR(3) = '0' then
                                                IncDec_16 <= "0101"; -- DE
                                        else
                                                IncDec_16 <= "1101";
                                        end if;
                                when 4 =>
                                        NoRead <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        when 11 => -- EG_11
                                -- CPI, CPD, CPIR, CPDR
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aXY;
                                        IncDec_16 <= "1100"; -- BC
                                when 2 =>
                                        Set_BusB_To <= "0110";
                                        Set_BusA_To(2 downto 0) <= "111";
                                        ALU_Op <= "0111";
                                        ALU_cpi <= '1';
                                        Save_ALU <= '1';
                                        PreserveC <= '1';
                                        if IR(3) = '0' then
                                                IncDec_16 <= "0110";
                                        else
                                                IncDec_16 <= "1110";
                                        end if;
                                when 3 =>
                                        NoRead <= '1';
                                        I_BC <= '1';
                                        TStates <= "101";
                                when 4 =>
                                        NoRead <= '1';
                                        TStates <= "101";
                                when others => null;
                                end case;
                        when 12 => -- EG_12
                                -- ED64 is TST A,n only while extensions are active.
                                if Tst_Active then
                                    ALU_Op<="0100";Set_BusA_To<="0111";Set_BusB_To<="0110";
                                    MCycles<="010";
                                    if MCycle="010" then Save_ALU<='1';Inc_PC<='1';end if;
                                elsif Exec_Control(EC_TSTIO)='1' and IntCycle='0' and NMICycle='0' then
                                    -- R25 TSTIO: M2 holds immediate in existing TmpAddr.L,
                                    -- M3 reads {00,C}; existing byte AND updates flags only.
                                    MCycles<="011";
                                    case to_integer(unsigned(MCycle)) is
                                    when 2 => Inc_PC<='1';LDZ<='1';Set_Addr_To<=aBC;
                                    when 3 => IORQ<='1';ALU_Op<="0100";
                                              Set_BusA_To<="1100";Set_BusB_To<="0110";Save_ALU<='1';
                                    when others => null;
                                    end case;
                                else
                                -- Locked/other-mode ED74 retains the legacy NEG alias.
                                -- NEG
                                Alu_OP <= "0010";
                                Set_BusB_To <= "0111";
                                Set_BusA_To <= "1010";
                                Read_To_Acc <= '1';
                                Save_ALU <= '1';
                                end if;
                        when 13 => -- EG_13
                                -- IM 0
                                IMode <= "00";
                        when 14 => -- EG_14
                                -- IM 1 (ED56)
                                IMode <= "01";
                        when 15 => -- EG_15
                                -- R20.6: SLP unsupported, execute as NOP when unlocked.
                                -- Locked Z80 retains its original ED76 IM1 alias.
                                if Exec_Control(EC_EXT)='0' then IMode <= "01";end if;
                        when 16 => -- EG_16
                                -- IM 2
                                IMode <= "10";
-- 16 bit arithmetic
                        when 17 => -- EG_17
                                -- ADC HL,ss
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        NoRead <= '1';
                                        ALU_Op <= "0001";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        Set_BusA_To(2 downto 0) <= "101";
                                        case to_integer(unsigned(IR(5 downto 4))) is
                                        when 0|1|2 =>
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                        Set_BusB_To(0) <= '1';
                                                when others =>
                                                Set_BusB_To <= "1000";
                                        end case;
                                        TStates <= "100";
                                when 3 =>
                                        NoRead <= '1';
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        ALU_Op <= "0001";
                                        Set_BusA_To(2 downto 0) <= "100";
                                        case to_integer(unsigned(IR(5 downto 4))) is
                                        when 0|1|2 =>
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusB_To(0) <= '0';
                                        when others =>
                                                Set_BusB_To <= "1001";
                                        end case;
                                when others =>
                                end case;
                        when 18 => -- EG_18
                                -- SBC HL,ss
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        NoRead <= '1';
                                        ALU_Op <= "0011";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        Set_BusA_To(2 downto 0) <= "101";
                                        case to_integer(unsigned(IR(5 downto 4))) is
                                        when 0|1|2 =>
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                                Set_BusB_To(0) <= '1';
                                        when others =>
                                                Set_BusB_To <= "1000";
                                        end case;
                                        TStates <= "100";
                                when 3 =>
                                        NoRead <= '1';
                                        ALU_Op <= "0011";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        Set_BusA_To(2 downto 0) <= "100";
                                        case to_integer(unsigned(IR(5 downto 4))) is
                                        when 0|1|2 =>
                                                Set_BusB_To(2 downto 1) <= IR(5 downto 4);
                                        when others =>
                                                        Set_BusB_To <= "1001";
                                        end case;
                                when others =>
                                end case;
                        when 19 => -- EG_19
                                -- RLD
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        NoRead <= '1';
                                        Set_Addr_To <= aXY;
                                when 3 =>
                                        Read_To_Reg <= '1';
                                        Set_BusB_To(2 downto 0) <= "110";
                                        Set_BusA_To(2 downto 0) <= "111";
                                        ALU_Op <= "1101";
                                        TStates <= "100";
                                        Set_Addr_To <= aXY;
                                        Save_ALU <= '1';
                                when 4 =>
                                        I_RLD <= '1';
                                        Legacy_Write <= '1';
                                when others =>
                                end case;
                        when 20 => -- EG_20
                                -- RRD
                                MCycles <= "100";
                                case to_integer(unsigned(MCycle)) is
                                when 2 =>
                                        Set_Addr_To <= aXY;
                                when 3 =>
                                        Read_To_Reg <= '1';
                                        Set_BusB_To(2 downto 0) <= "110";
                                        Set_BusA_To(2 downto 0) <= "111";
                                        ALU_Op <= "1110";
                                        TStates <= "100";
                                        Set_Addr_To <= aXY;
                                        Save_ALU <= '1';
                                when 4 =>
                                        I_RRD <= '1';
                                        Legacy_Write <= '1';
                                when others =>
                                end case;
                        when 21 => -- EG_21
                                -- RETI, RETN
                                MCycles <= "011";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_TO <= aSP;
                                when 2 =>
                                        IncDec_16 <= "0111";
                                        Set_Addr_To <= aSP;
                                        LDZ <= '1';
                                when 3 =>
                                        Jump <= '1';
                                        IncDec_16 <= "0111";
                                        I_RETN <= '1';
                                when others => null;
                                end case;
                        when 22 => -- EG_22
                                -- IN r,(C)
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aBC;
                                when 2 =>
                                        IORQ <= '1';
                                        if IR(5 downto 3) /= "110" then
                                                Read_To_Reg <= '1';
                                                Set_BusA_To(2 downto 0) <= IR(5 downto 3);
                                        end if;
                                        I_INRC <= '1';
                                when others =>
                                end case;
                        when 23 => -- EG_23
                                -- OUT (C),r
                                -- OUT (C),0
                                MCycles <= "010";
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aBC;
                                        Set_BusB_To(2 downto 0) <= IR(5 downto 3);
                                        if IR(5 downto 3) = "110" then
                                                Set_BusB_To(3) <= '1';
                                        end if;
                                when 2 =>
                                        Legacy_Write <= '1';
                                        IORQ <= '1';
                                when others =>
                                end case;
                        when 24 => -- EG_24
                                -- INI, IND, INIR, INDR. R23.2: ED84/8C are NOP above.
                                if IR(2)='0' or Block_IO2 then
                                MCycles <= "100";if Block_IO2 then MCycles<="110";end if;
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        Set_Addr_To <= aBC;
                                        if not Block_IO2 then
                                        Set_BusB_To <= "1010";
                                        Set_BusA_To <= "0000";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        ALU_Op <= "0010";
                                        end if;
                                when 2 =>
                                        IORQ <= '1';
                                        Set_BusB_To <= "0110";
                                        Set_Addr_To <= aXY;
                                when 3 =>
                                        if IR(3) = '0' then
                                                IncDec_16 <= "0110";    -- 0242a
                                        else
                                                IncDec_16 <= "1110";    -- 0242a
                                        end if;
                                        TStates <= "100";
                                        Legacy_Write <= '1';
                                        if not Block_IO2 then I_BTR <= '1';end if;
                                when 4 =>
                                        NoRead <= '1';TStates <= "101";
                                        if Block_IO2 then
                                            Set_BusA_To<="0000";Set_BusB_To<="1010";ALU_Op<="0010";
                                            Read_To_Reg<='1';Save_ALU<='1';
                                        end if;
                                when 5 =>
                                        NoRead<='1';
                                        if Block_IO2 then
                                            Set_BusA_To<="0001";Set_BusB_To<="1010";
                                            if IR(3)='0' then ALU_Op<="0000";else ALU_Op<="0010";end if;
                                            Read_To_Reg<='1';Save_ALU<='1';
                                        end if;
                                when 6 => NoRead<='1';
                                when others => null;
                                end case;
                        end if;
                        when 25 => -- EG_25
                                -- OUTI, OUTD, OTIR, OTDR. R23.2: EDA4/AC are NOP above.
                                if IR(2)='0' or Block_IO2 then
                                MCycles <= "100";if Block_IO2 then MCycles<="110";end if;
                                case to_integer(unsigned(MCycle)) is
                                when 1 =>
                                        TStates <= "101";
                                        Set_Addr_To <= aXY;
                                        if not Block_IO2 then
                                        Set_BusB_To <= "1010";
                                        Set_BusA_To <= "0000";
                                        Read_To_Reg <= '1';
                                        Save_ALU <= '1';
                                        ALU_Op <= "0010";
                                        end if;
                                when 2 =>
                                        Set_BusB_To <= "0110";
                                        Set_Addr_To <= aBC;
                                when 3 =>
                                        if IR(3) = '0' then
                                                IncDec_16 <= "0110";    -- 0242a
                                        else
                                                IncDec_16 <= "1110";    -- 0242a
                                        end if;
                                        IORQ <= '1';
                                        Legacy_Write <= '1';
                                        if not Block_IO2 then I_BTR <= '1';end if;
                                when 4 =>
                                        NoRead <= '1';TStates <= "101";
                                        if Block_IO2 then
                                            Set_BusA_To<="0000";Set_BusB_To<="1010";ALU_Op<="0010";
                                            Read_To_Reg<='1';Save_ALU<='1';
                                        end if;
                                when 5 =>
                                        NoRead<='1';
                                        if Block_IO2 then
                                            Set_BusA_To<="0001";Set_BusB_To<="1010";
                                            if IR(3)='0' then ALU_Op<="0000";else ALU_Op<="0010";end if;
                                            Read_To_Reg<='1';Save_ALU<='1';
                                        end if;
                                when 6 => NoRead<='1';
                                when others => null;
                                end case;
                                end if;
                        when 26 => -- EG_26
                                --R800 MULUB
                                null;
                        when 27 => -- EG_27
                                --R800 MULUW
                                null;
                        when others => null;
                end case;

                end case;

                if not Indexed_Pair_Active and not Block_IO2 then
                if Mode = 1 then
                        if MCycle = "001" then
--                              TStates <= "100";
                        else
                                TStates <= "011";
                        end if;
                end if;

                if Mode = 3 then
                        if MCycle = "001" then
--                              TStates <= "100";
                        else
                                TStates <= "100";
                        end if;
                end if;

                if Mode < 2 then
                        if MCycle = "110" then
                                if not Tst_Active then Inc_PC <= '1';end if;
                                if Mode = 1 then
                                        Set_Addr_To <= aXY;
                                        TStates <= "100";
                                        Set_BusB_To(2 downto 0) <= SSS;
                                        Set_BusB_To(3) <= '0';
                                end if;
                                if IRB = "00110110" or IRB = "11001011" then
                                        Set_Addr_To <= aNone;
                                end if;
                        end if;
                        if MCycle = "111" then
                                if Mode = 0 then
                                        TStates <= "101";
                                end if;
                                if not Tst_Active then
                                if ISet /= "01" then
                                        Set_Addr_To <= aXY;
                                end if;
                                Set_BusB_To(2 downto 0) <= SSS;
                                Set_BusB_To(3) <= '0';
                                if IRB = "00110110" or ISet = "01" then
                                        -- LD (HL),n
                                        Inc_PC <= '1';
                                else
                                        NoRead <= '1';
                                end if;
                                end if;
                        end if;
                end if;


                -- R1 only: explicit suffixes, immediate register loads, byte data access.
                if Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
                    if Exec_Control(EC_WIDTH_PREFIX)='1' then
                        Prefix<="11";
                    end if;
                    if Exec_Control(EC_IMM_LONG)='1' then
                        MCycles<="100";
                        if MCycle="100" then Inc_PC<='1'; Read_To_Reg<='0'; end if;
                    end if;
                    -- Readback of the separate SPL, into bank-00 diagnostic memory.
                    -- Only LD.LIS (nn),SP (49 ED 73 nn nn) is in the R1 subset.
                    if Exec_Control(EC_SP_READ)='1' then
                        MCycles<="110";
                        if MCycle="101" then
                            Inc_WZ<='1'; Set_Addr_To<=aZI; Set_BusB_To<="1110";
                        elsif MCycle="110" then
                            Inc_PC<='0'; Set_Addr_To<=aNone; NoRead<='0'; null;
                        end if;
                    end if;
                end if;


                -- R2 explicit long PUSH/POP. SPL only; never changes SPS or PC.
                if Exec_Control(EC_STACK)='1' and Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="100"; null;Read_To_Reg<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    TStates<="011"; if MCycle="001" then TStates<="100";end if;
                    if Exec_Control(EC_STACK_PUSH)='1' then
                        case to_integer(unsigned(MCycle)) is
                        when 1 => TStates<="101";IncDec_16<="1111";Set_Addr_To<=aSP;
                            if Exec_Control(EC_PAIR_SP)='1' then Set_BusB_To<="0111";else Set_BusB_To<='0' & DPair & '0';end if;
                        when 2 => null;IncDec_16<="1111";Set_Addr_To<=aSP;
                            if Exec_Control(EC_PAIR_SP)='1' then Set_BusB_To<="0111";else Set_BusB_To<='0' & DPair & '0';end if;
                        when 3 => null;IncDec_16<="1111";Set_Addr_To<=aSP;
                            if Exec_Control(EC_PAIR_SP)='1' then Set_BusB_To<="1011";else Set_BusB_To<='0' & DPair & '1';end if;
                        when 4 => null;
                        when others=>null;
                        end case;
                    else
                        case to_integer(unsigned(MCycle)) is
                        when 1=>Set_Addr_To<=aSP;
                        when 2=>IncDec_16<="0111";Set_Addr_To<=aSP;Read_To_Reg<='1';
                            if Exec_Control(EC_PAIR_SP)='1' then Set_BusA_To<="1011";else Set_BusA_To<='0' & DPair & '1';end if;
                        when 3=>IncDec_16<="0111";Set_Addr_To<=aSP;Read_To_Reg<='1';
                            if Exec_Control(EC_PAIR_SP)='1' then Set_BusA_To<="0111";else Set_BusA_To<='0' & DPair & '0';end if;
                        when 4=>IncDec_16<="0111";
                        when others=>null;
                        end case;
                    end if;
                end if;

                -- R3 pair absolute transfers: separate immediate width and data width.
                if Exec_Control(EC_PAIR_ABS)='1' and Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
                    if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
                    if Data_Long='1' then countdata:=3;else countdata:=2;end if;
                    if Exec_Control(EC_PAGE_BASE)='1' then pairnum:="10";else pairnum:=IR(5 downto 4);end if;
                    cycle:=to_integer(unsigned(MCycle));reading:=IR(3)='1';
                    MCycles<=std_logic_vector(to_unsigned(lastaddr+countdata,3));
                    null;Read_To_Reg<='0';Read_To_Acc<='0';Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';
                    Set_Addr_To<=aNone;NoRead<='0';IncDec_16<="0000";
                    if cycle=1 then TStates<="100";else TStates<="011";end if;
                    if cycle=2 then Inc_PC<='1';LDZ<='1';end if;
                    if cycle=3 then Inc_PC<='1';LDW<='1';end if;
                    if cycle=4 and lastaddr=4 then Inc_PC<='1';end if;
                    if cycle=lastaddr then
                        Set_Addr_To<=aZI;
                        if Exec_Control(EC_ABS_SP)='1' then Set_BusB_To<="1000";else Set_BusB_To<='0' & pairnum & '1';end if;
                    elsif cycle>lastaddr then
                        if cycle<lastaddr+countdata then Inc_WZ<='1';Set_Addr_To<=aZI;end if;
                        if reading then
                            if cycle=lastaddr+1 then
                                Read_To_Reg<='1';if Exec_Control(EC_ABS_SP)='1' then Set_BusA_To<="1000";else Set_BusA_To<='0' & pairnum & '1';end if;
                            elsif cycle=lastaddr+2 then
                                Read_To_Reg<='1';if Exec_Control(EC_ABS_SP)='1' then Set_BusA_To<="1001";else Set_BusA_To<='0' & pairnum & '0';end if;
                            end if;
                        else
                            null;
                            if cycle=lastaddr+1 then
                                if Exec_Control(EC_ABS_SP)='1' then Set_BusB_To<="1001";else Set_BusB_To<='0' & pairnum & '0';end if;
                            elsif cycle=lastaddr+2 then Set_BusB_To<="1110";end if;
                        end if;
                    end if;
                end if;

                -- R4 absolute byte access: immediate width independent from data block.
                if Exec_Control(EC_BYTE_ABS)='1' and Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
                    if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
                    cycle:=to_integer(unsigned(MCycle));MCycles<=std_logic_vector(to_unsigned(lastaddr+1,3));
                    Inc_PC<='0';LDZ<='0';LDW<='0';null;Read_To_Acc<='0';Read_To_Reg<='0';
                    Set_Addr_To<=aNone;Inc_WZ<='0';IncDec_16<="0000";NoRead<='0';
                    if cycle=1 then TStates<="100";else TStates<="011";end if;
                    if cycle=2 then Inc_PC<='1';LDZ<='1';end if;
                    if cycle=3 then Inc_PC<='1';LDW<='1';end if;
                    if cycle=4 and lastaddr=4 then Inc_PC<='1';end if;
                    if cycle=lastaddr then Set_Addr_To<=aZI;Set_BusB_To<="0111";
                    elsif cycle=lastaddr+1 then
                        if Exec_Control(EC_BYTE_STORE)='1' then null;else Read_To_Acc<='1';end if;
                    end if;
                end if;
                -- R4 EX(SPL),HL/IX/IY. Read all 3 bytes, then write all 3 bytes.
                -- SPL is never changed. The register commits after the final write.
                if Exec_Control(EC_EX_SP)='1' and Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="111";Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";
                    null;Read_To_Reg<='0';Read_To_Acc<='0';Set_Addr_To<=aSP;NoRead<='0';
                    ExchangeDH<='0';ExchangeRp<='0';
                    if MCycle="001" then TStates<="100";else TStates<="011";end if;
                    case MCycle is
                    when "100"=>null;
                    when "101"=>null;
                    when "110"=>null;
                    when "111"=>null;Set_Addr_To<=aNone;
                    when others=>null;
                    end case;
                end if;

                -- R5 long ADD/ADC/SBC. Internal T4 operand capture, T7 atomic result.
                -- Short and locked profiles retain the original 8-bit ALU schedule.
                if Exec_Control(EC_ARITH)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="111";NoRead<='1';null;Read_To_Reg<='0';Read_To_Acc<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Arith16<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                end if;

                -- MLT replaces only the four NEG aliases while the extension gate is open.
                -- One captured 8x8 multiply is committed at T7, flags and upper byte preserved.
                if Exec_Control(EC_MUL)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="111";NoRead<='1';null;Read_To_Reg<='0';Read_To_Acc<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Arith16<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                end if;

                -- LEA/PEA consume one displacement byte, regardless of Stream_Long.
                if Exec_Control(EC_EA)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="010";TStates<="011";if MCycle="001" then TStates<="100";end if;
                    NoRead<='0';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Arith16<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Set_Addr_To<=aNone;LDZ<='0';LDW<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';I_RETN<='0';IMode<="11";
                    Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                    if MCycle="010" then Inc_PC<='1';TStates<="101";end if;
                    if Exec_Control(EC_PEA)='1' then
                        if Data_Long='1' then MCycles<="101";else MCycles<="100";end if;
                        if MCycle="010" or MCycle="011" or (MCycle="100" and Data_Long='1') then
                            IncDec_16<="1111";Set_Addr_To<=aSP;
                        end if;
                        if unsigned(MCycle)>=3 then null;end if;
                    end if;
                end if;

                -- Stage-5 transition: JP.LIL enters ADL, JP.SIS returns to Z80.
                if Exec_Control(EC_JP)='1' and IntCycle='0' and NMICycle='0' then
                    if Stream_Long='1' then MCycles<="100";else MCycles<="011";end if;
                    TStates<="011";if MCycle="001" then TStates<="100";end if;
                    NoRead<='0';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Jump<='0';Inc_PC<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";
                    if MCycle="010" then Inc_PC<='1';LDZ<='1';end if;
                    if MCycle="011" then Inc_PC<='1';LDW<='1';end if;
                    if MCycle="100" then Inc_PC<='1';end if;
                end if;
                if Exec_Control(EC_ADL_ED_ALIAS)='1' then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';null;Jump<='0';I_RETN<='0';
                    IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;

                -- Native ADL CALL/RET/RST use only a 3-byte SPL frame, no mode byte.
                if Exec_Control(EC_NATIVE_CTRL)='1' and IntCycle='0' and NMICycle='0' then
                    TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';JumpE<='0';I_DJNZ<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    if Exec_Control(EC_CALL_KIND)='1' then
                        -- M2..M4 target bytes, M5..M7 return PC bytes (upper first).
                        if Exec_Control(EC_UNCOND_FLOW)='1' or Branch_Condition='1' then
                            MCycles<="111";
                            if MCycle="100" or MCycle="101" or MCycle="110" then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                            if unsigned(MCycle)>=5 then null;end if;
                        else MCycles<="100";end if;
                        if unsigned(MCycle)>=2 and unsigned(MCycle)<=4 then Inc_PC<='1';end if;
                    elsif Exec_Control(EC_RET_KIND)='1' then
                        if Exec_Control(EC_UNCOND_FLOW)='1' or Branch_Condition='1' then
                            MCycles<="100";
                            if unsigned(MCycle)<=3 then Set_Addr_To<=aSP;end if;
                            if unsigned(MCycle)>=2 then IncDec_16<="0111";end if;
                        else MCycles<="001";NoRead<='1';end if;
                    else
                        MCycles<="100";
                        if unsigned(MCycle)<=3 then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                        if unsigned(MCycle)>=2 then null;end if;
                    end if;
                end if;
                -- Mixed CALL/RET/RST suffix frames belong to stage8, not this native path.
                if Exec_Control(EC_MIX_CTRL)='1' then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';null;
                    Jump<='0';Call<='0';RstP<='0';IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                    if Exec_Control(EC_MIX_SUPPORTED)='1' and IntCycle='0' and NMICycle='0' then
                        Halt<='0';Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';
                    end if;
                end if;

                -- R11 native ADL interrupt frame. IRQ M1 remains a real IACK.
                if Interrupt_Long='1' then
                    MCycles<="100";if IntCycle='1' and Interrupt_Mode="10" then MCycles<="111";end if;
                    TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Halt<='0';SetEI<='0';SetDI<='0';Special_LD<="000";IMode<="11";
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';JumpE<='0';I_DJNZ<='0';I_RETN<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;Prefix<="00";
                    if unsigned(MCycle)<=3 then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                    if MCycle="010" or MCycle="011" or MCycle="100" then null;end if;
                end if;
                if Exec_Control(EC_IRQ_RETURN)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="100";TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Jump<='0';I_RETN<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    if unsigned(MCycle)<=3 then Set_Addr_To<=aSP;end if;
                    if unsigned(MCycle)>=2 then IncDec_16<="0111";end if;
                end if;
                if Exec_Control(EC_IV_PAIR)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="101";NoRead<='1';null;Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Inc_PC<='0';IncDec_16<="0000";Set_Addr_To<=aNone;Set_BusA_To<="0100";Special_LD<="000";
                end if;
                -- R12: replace undocumented ED aliases while extensions are enabled.
                -- Actual transfer is ADL-only and preserves all flags.
                if Exec_Control(EC_MB_OPCODE)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="101";NoRead<='1';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Set_Addr_To<=aNone;LDZ<='0';LDW<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';I_RETN<='0';IMode<="11";
                    SetDI<='0';SetEI<='0';Halt<='0';Special_LD<="000";Arith16<='0';
                end if;
                -- R13 MADL controls are valid in either current memory mode.
                if Exec_Control(EC_MADL_OPCODE)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="101";NoRead<='1';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Set_Addr_To<=aNone;LDZ<='0';LDW<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';I_RETN<='0';IMode<="11";
                    SetDI<='0';SetEI<='0';Halt<='0';Special_LD<="000";Arith16<='0';
                end if;
                -- Mode-bearing RETI.L/RETN.L frames remain stage8 work.
                if Exec_Control(EC_MIX_IRQ_RETURN)='1' and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';null;Jump<='0';I_RETN<='0';
                    IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;
                end if; -- R17: legacy XY/extension overrides
                -- R24.2: read requests and cycle counts are unchanged. The pair
                -- collector performs one architectural write at the final byte.
                if (Exec_Control(EC_LOAD_IMM)='1' or Exec_Control(EC_LOAD_ABS)='1' or Exec_Control(EC_LOAD_IND)='1') and IntCycle='0' and NMICycle='0' then
                    Read_To_Reg<='0';Set_BusA_To<="0000";
                end if;
        end process;

    -- The legacy writer is unchanged. Extension overrides select one opcode
    -- class in parallel instead of chaining every instruction's Write mux.
    process(Exec_Control, Interrupt_Long, Legacy_Write, Write_Class, ISet, MCycle, Ext_Active, Data_Long,
            Stream_Long, ADL_Mode, Has_Width, IntCycle, NMICycle, Branch_Condition, XY_State)
        variable w : std_logic;
        variable base_kind, ed_kind : std_logic_vector(3 downto 0);
        variable lastaddr, cycle : integer range 0 to 7;
    begin
        w:=Legacy_Write; base_kind:=Write_Class(3 downto 0);ed_kind:=Write_Class(7 downto 4);
        cycle:=to_integer(unsigned(MCycle));
        if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
        if Exec_Control(EC_EXT_MODE0)='1' and IntCycle='0' and NMICycle='0' then
            if ISet="00" then
                case base_kind is
                when x"1"|x"2" =>
                    if Exec_Control(EC_ANY_LONG)='1' then
                        w:='0';if base_kind=x"1" and cycle>lastaddr then w:='1';end if;
                    end if;
                when x"3"|x"4" =>
                    if Exec_Control(EC_ANY_LONG)='1' then
                        w:='0';if base_kind=x"3" and cycle=lastaddr+1 then w:='1';end if;
                    end if;
                when x"5"|x"6" =>
                    if Data_Long='1' then
                        w:='0';if base_kind=x"5" and cycle>=2 and cycle<=4 then w:='1';end if;
                    end if;
                when x"7" =>
                    if Data_Long='1' then w:='0';if cycle>=5 then w:='1';end if;end if;
                when x"8" => if Data_Long='1' then w:='0';end if;
                when others=>null;
                end case;
            elsif ISet="10" then
                case ed_kind is
                when x"1"|x"2" =>
                    if Exec_Control(EC_ANY_LONG)='1' then
                        w:='0';if ed_kind=x"1" and cycle>lastaddr then w:='1';end if;
                    end if;
                when x"3" => if Data_Long='1' then w:='0';end if;
                when x"A" => w:='0';if cycle>=2 and (cycle<=3 or (cycle=4 and Data_Long='1')) then w:='1';end if;
                when x"B" => w:='0';
                when x"4"|x"5" => w:='0';
                when x"6" => w:='0';if cycle>=3 then w:='1';end if;
                when others=>null;
                end case;
            end if;
        end if;
        -- Preserve the original guards, including profiles with Mode/=0,
        -- a closed extension gate, or an interrupt coincident with a suffix.
        if Exec_Control(EC_EXT_BASE)='1' and IntCycle='0' and NMICycle='0' then
            if Exec_Control(EC_JP)='1' then w:='0';end if;
            if Exec_Control(EC_NATIVE_CTRL)='1' then
                case base_kind is
                when x"A"|x"B" =>
                    w:='0';if cycle>=5 and (base_kind=x"A" or Branch_Condition='1') then w:='1';end if;
                when x"C"|x"D" => w:='0';
                when x"E" => w:='0';if cycle>=2 then w:='1';end if;
                when others=>null;
                end case;
            end if;
        end if;
        if Exec_Control(EC_ADL_ED_ALIAS)='1' then w:='0';end if;
        if Exec_Control(EC_MIX_CTRL)='1' then w:='0';end if;
        if Interrupt_Long='1' then
            w:='0';if cycle>=2 and cycle<=4 then w:='1';end if;
        end if;
        if Exec_Control(EC_ED_NO_WRITE)='1' and IntCycle='0' and NMICycle='0' then w:='0';end if;
        if Exec_Control(EC_PAIR_INDEX)='1' and IntCycle='0' and NMICycle='0' then
            w:='0';if ed_kind=x"A" and cycle>=3 and (cycle<=4 or (cycle=5 and Data_Long='1')) then w:='1';end if;
        end if;
        Write<=w;
    end process;

end;
