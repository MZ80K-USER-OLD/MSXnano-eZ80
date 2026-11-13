--
-- Z80 compatible microprocessor core, asynchronous top level
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
--  0211 : Fixed interrupt cycle
--  0235 : Updated for T80_eZ80 interface change
--  0238 : Updated for T80_eZ80 interface change
--  0240 : Updated for T80_eZ80 interface change
--  0242 : Updated for T80_eZ80 interface change
--  0247 : Fixed bus req/ack cycle
--  0247a: 7th of September, 2003 by Kazuhiro Tsujikawa (tujikawa@hat.hi-ho.ne.jp)
--         Fixed IORQ_n, RD_n, WR_n bus timing
--  0250 : Added R800 Multiplier by TobiFlex 2017.10.15
--
--  +k01 : Added RstKeyLock and swioRESET_n by KdL 2010.10.25
--  +k02 : Added R800_mode signal by KdL 2018.05.14
--  +k03 : RstKeyLock and swioRESET_n were put back outside of T80_eZ80 by KdL 2019.05.20
--  +k04 : Separation of T800 from T80_eZ80 by KdL 2021.02.01
--

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.T80_eZ80_Pack.all;

entity G80A_eZ80 is
    generic(
        Mode        : integer := 0;     -- 0 => Z80, 1 => Fast Z80, 2 => 8080, 3 => GB
        DATA_EXTENDED : boolean := true;
        DIAGNOSTICS : boolean := false;
        IOWait      : integer := 1      -- 0 => Single I/O cycle, 1 => Std I/O cycle
    );
    port(
        RESET_n     : in std_logic;
        CLK_n       : in std_logic;
		clk_enable  : in std_logic;
		clk_falling	: in std_logic;
        WAIT_n      : in std_logic;
        INT_n       : in std_logic;
        NMI_n       : in std_logic;
        BUSRQ_n     : in std_logic;
        M1_n        : out std_logic;
        MREQ_n      : out std_logic;
        IORQ_n      : out std_logic;
        RD_n        : out std_logic;
        WR_n        : out std_logic;
        RFSH_n      : out std_logic;
        HALT_n      : out std_logic;
        BUSAK_n     : out std_logic;
        A           : out std_logic_vector(15 downto 0);
        A24 : out std_logic_vector(23 downto 0);
		update_addr	: out std_logic;
        DI           : in std_logic_vector(7 downto 0);
        DO           : out std_logic_vector(7 downto 0);
        Data_Reverse: out std_logic;
        A_MSX : out std_logic_vector(15 downto 0);
        Extended_Window : out std_logic
    );
end G80A_eZ80;

architecture rtl of G80A_eZ80 is

    signal Diag_Select : std_logic_vector(7 downto 0);
    signal Diag_Read : std_logic_vector(7 downto 0);
    signal Diag_Active, Diag_IRQ, Diag_NMI_Arm, HALT_i : std_logic;
    signal Diag_NMI_Count : unsigned(3 downto 0);
    signal INT_Input_n, NMI_Input_n, Vector_Window : std_logic;
    signal Diag_IACK_Byte, Instruction_Data : std_logic_vector(7 downto 0);
    signal Bank_i : std_logic_vector(7 downto 0);
    signal Extension_State_i : std_logic;
    signal MADL_i : std_logic;
    signal MBASE_i : std_logic_vector(7 downto 0);
    signal CEN          : std_logic;
    signal Reset_s      : std_logic;
    signal IntCycle_n   : std_logic;
    signal IORQ         : std_logic;
    signal NoRead       : std_logic;
    signal Write        : std_logic;
    signal MREQ         : std_logic;
    signal MReq_Inhibit : std_logic;
    signal IReq_Inhibit : std_logic;        -- 0247a
    signal Req_Inhibit  : std_logic;
    signal RD           : std_logic;
    signal MREQ_n_i     : std_logic;
    signal IORQ_n_i     : std_logic;
    signal RD_n_i       : std_logic;
    signal WR_n_i       : std_logic;
    signal WR_n_j       : std_logic;        -- 0247a
    signal RFSH_n_i     : std_logic;
    signal BUSAK_n_i    : std_logic;
    signal A_i          : std_logic_vector(15 downto 0);
    signal Core_DO, Request_Data : std_logic_vector(7 downto 0);
    signal Request_Address : std_logic_vector(23 downto 0);
    signal Request_Write, Request_IO : std_logic;
    signal Request_MSX_Address : std_logic_vector(15 downto 0);
    signal Request_Extended : std_logic;
    signal DI_Reg       : std_logic_vector (7 downto 0);    -- Input synchroniser
    signal Wait_s       : std_logic;
    signal MCycle       : std_logic_vector(2 downto 0);
    signal TState       : std_logic_vector(2 downto 0);

begin
    -- R19 test hook: use the existing selector FF, no extra opcode register.
    Diag_IACK_Byte<="11" & Diag_Select(2 downto 0) & "111" when Diag_Select(7 downto 3)="11100" else
        x"CD" when Diag_Select=x"E8" else x"76" when Diag_Select=x"E9" else
        x"FB" when Diag_Select=x"EA" else x"5B" when Diag_Select=x"EB" else x"FE";

	--CEN <= '1';
    Instruction_Data<=Diag_IACK_Byte when DIAGNOSTICS and Diag_Active='1' and IntCycle_n='0' and MCycle="001" else DI;
    CEN <= clk_enable;

    BUSAK_n <= BUSAK_n_i;
    MREQ_n_i <= not MREQ or (Req_Inhibit and MReq_Inhibit);
    RD_n_i <= not RD or Req_Inhibit;
    WR_n_j <= WR_n_i;                                                   -- 0247a

    MREQ_n <= MREQ_n_i when BUSAK_n_i = '1' else 'Z';
    IORQ_n <= IORQ_n_i or IReq_Inhibit when BUSAK_n_i = '1' else 'Z';   -- 0247a
    RD_n <= RD_n_i when BUSAK_n_i = '1' else 'Z';
    WR_n <= WR_n_j when BUSAK_n_i = '1' else 'Z';                       -- 0247a
    RFSH_n <= RFSH_n_i when BUSAK_n_i = '1' else 'Z';
    -- Decode read intent before MREQ/T1, so the existing bridge can assert
    -- WAIT before RD. Captured SDRAM requests remain untouched downstream.
    Vector_Window <= '1' when DIAGNOSTICS and Diag_Active='1' and Bank_i=x"00" and A_i(15 downto 7)="000000000" and
        Write='0' and IORQ='0' and IntCycle_n='1' and RFSH_n_i='1' else '0';
    -- R11.6: latch the final read-only vector decision in one bit at T1.
    -- Low16 address payload registers do not depend on the core Write decode.
    -- Only the refresh phase uses the core's refresh address directly.
    -- All ordinary requests retain their T1 address through WAIT and bus release.
    A24 <= x"00" & A_i when RFSH_n_i='0' and BUSAK_n_i='1' else
           Request_Address when BUSAK_n_i='1' else (others=>'Z');
    -- R11.6: capture MSX payload and final isolation at the same T1 edge.
    -- Refresh remains bank zero; ordinary addresses never use a live bank mux.
    A_MSX <= A_i when RFSH_n_i='0' and BUSAK_n_i='1' else
             x"0000" when Request_Extended='1' and BUSAK_n_i='1' else
             Request_MSX_Address when BUSAK_n_i='1' else (others=>'Z');
    Extended_Window <= '0' when RFSH_n_i='0' else Request_Extended;
    DO <= Request_Data;
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then
            Request_Address <= (others=>'0'); Request_Data <= (others=>'0');
            Request_Write <= '0'; Request_IO <= '0';
            Request_MSX_Address <= (others=>'0'); Request_Extended <= '0';
        elsif falling_edge(CLK_n) then
            if clk_falling='1' then
                if TState="001" then
                    Request_Address <= Bank_i & A_i;
                    if Vector_Window='1' then
                        Request_Address <= x"0F" & A_i;
                    end if;
                    Request_MSX_Address <= (others=>'0'); Request_Extended <= '1';
                    if Bank_i=x"00" then
                        Request_MSX_Address <= A_i; Request_Extended <= Vector_Window;
                    end if;
                    if IORQ='1' or (IntCycle_n='0' and MCycle="001") then
                        Request_Address <= x"00" & A_i;
                        Request_MSX_Address <= A_i; Request_Extended <= '0';
                    end if;
                    Request_Write <= Write; Request_IO <= IORQ;
                end if;
                -- Core data can be refreshed during an automatic T1 wait.
                -- It is final before the memory write strobe at T2.
                if TState="001" or TState="010" then Request_Data <= Core_DO; end if;
            end if;
        end if;
    end process;
    HALT_n<=HALT_i;
    INT_Input_n <= not Diag_IRQ when DIAGNOSTICS and Diag_Active='1' else INT_n;
    NMI_Input_n <= '0' when DIAGNOSTICS and Diag_NMI_Count/=0 else NMI_n;
    process(Diag_Select, Extension_State_i, MBASE_i, MADL_i)
    begin
        Diag_Read<="1110000" & Extension_State_i;
        if Extension_State_i='1' then
            case Diag_Select is
            when x"C0"=>Diag_Read<=x"45";
            when x"C1"=>Diag_Read<=x"5A";
            when x"C2"=>Diag_Read<=x"02";
            when x"C3"=>Diag_Read<=x"A7";
            when x"C4"=>Diag_Read<=x"FF";
            when x"C5"=>if DIAGNOSTICS then Diag_Read<=x"8F";else Diag_Read<=x"0F";end if;
            when x"C6"=>Diag_Read<=x"00";
            when x"C7"=>if DIAGNOSTICS then Diag_Read<=x"70";else Diag_Read<=x"F0";end if;
            when x"C8"=>Diag_Read<=MBASE_i;
            when x"C9"=>Diag_Read<="0000000" & MADL_i;
            when x"CA"=>Diag_Read<=x"01"; -- R19 ADL/MADL IM0 engine
            when x"CB"=>Diag_Read<=x"FE";
            when others=>null;
            end case;
        end if;
    end process;
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then
            Diag_Select<=x"FF";Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
        elsif rising_edge(CLK_n) then
            if clk_enable='1' then
                if Diag_NMI_Count/=0 then Diag_NMI_Count<=Diag_NMI_Count-1;end if;
                if DIAGNOSTICS and Diag_Active='1' and Diag_NMI_Arm='1' and HALT_i='0' then
                    Diag_NMI_Count<=to_unsigned(8,4);Diag_NMI_Arm<='0';
                end if;
                if Extension_State_i='0' then
                    Diag_Select<=x"FF";Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                end if;
                if IORQ='1' and Write='1' and A_i=x"E7E7" and TState="011" then
                    if Core_DO=x"A5" or Core_DO=x"5A" or Core_DO=x"00" then Diag_Select<=x"FF";
                    elsif Extension_State_i='1' then
                        if Core_DO(7 downto 4)=x"C" or (DIAGNOSTICS and Diag_Active='1' and Core_DO(7 downto 4)=x"E") then Diag_Select<=Core_DO;
                        elsif DIAGNOSTICS then
                            case Core_DO is
                            when x"D8"=>Diag_Active<='1';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when x"D1"=>if Diag_Active='1' then Diag_IRQ<='1';end if;
                            when x"D2"=>if Diag_Active='1' then Diag_NMI_Arm<='1';end if;
                            when x"D4"=>Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when x"D0"=>Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when others=>null;
                            end case;
                        end if;
                    end if;
                end if;
            end if;
        end if;
    end process;
    A <= A_i when BUSAK_n_i = '1' else (others => 'Z');
    --D <= DO when Write = '1' and BUSAK_n_i = '1' else (others => 'Z');
    Data_Reverse <= Request_Write;

    process (RESET_n, CLK_n)
    begin
        if RESET_n = '0' then
            Reset_s <= '0';
        elsif CLK_n'event and CLK_n = '1' then
			if clk_enable = '1' then
				Reset_s <= '1';
			end if;
        end if;
    end process;

    u0 : T80_eZ80
        generic map(
            DATA_EXTENDED=>DATA_EXTENDED,
            Mode => Mode,
            IOWait => IOWait)
        port map(
            CEN => CEN,
            M1_n => M1_n,
            IORQ => IORQ,
            NoRead => NoRead,
            Write => Write,
            RFSH_n => RFSH_n_i,
            HALT_n => HALT_i,
            WAIT_n => Wait_s,
            INT_n => INT_Input_n,
            NMI_n => NMI_Input_n,
            RESET_n => Reset_s,
            BUSRQ_n => BUSRQ_n,
            BUSAK_n => BUSAK_n_i,
            CLK_n => CLK_n,
            A => A_i, A_BANK=>Bank_i, Extension_State=>Extension_State_i, MBASE_State=>MBASE_i, MADL_State=>MADL_i,
			update_addr => update_addr,
            DInst => Instruction_Data,
            DI => DI_Reg,
            DO => Core_DO,
            MC => MCycle,
            TS => TState,
            IntCycle_n => IntCycle_n);

    process (CLK_n)
    begin
        if CLK_n'event and CLK_n = '0' then
			if clk_falling = '1' then
				Wait_s <= WAIT_n;
				if TState = "011" and BUSAK_n_i = '1' then
					if Request_Address(15 downto 0)=x"E7E7" and Request_IO='1' and Request_Write='0' and IntCycle_n='1' then DI_Reg<=Diag_Read;
                    elsif DIAGNOSTICS and Diag_Active='1' and IntCycle_n='0' and MCycle="001" then DI_Reg<=Diag_IACK_Byte;
                    else DI_Reg <= to_x01(DI);end if;
				end if;
			end if;
        end if;
    end process;

    process (CLK_n)                         -- 0247a
    begin
        if CLK_n'event and CLK_n = '1' then
			if clk_enable = '1' then
				-- Preserve I/O qualification, but allow the interrupt acknowledge cycle.
                IReq_Inhibit <= not (IORQ or not IntCycle_n);
			end if;
        end if;
    end process;

    process (Reset_s,CLK_n)                 -- 0247a
    begin
        if Reset_s = '0' then
            WR_n_i <= '1';
        elsif CLK_n'event and CLK_n = '0' then
			if clk_falling = '1' then
				if (IORQ = '0') then
					if TState = "010" then
						WR_n_i <= not Request_Write;
					elsif Tstate = "011" then
						WR_n_i <= '1';
					end if;
				else
					if TState = "001" and IORQ_n_i = '0' then
						WR_n_i <= not Request_Write;
					elsif Tstate = "011" then
						WR_n_i <= '1';
					end if;
				end if;
			end if;
        end if;
    end process;

    process (Reset_s,CLK_n)                 -- 0247a
    begin
        if Reset_s = '0' then
            Req_Inhibit <= '0';
        elsif CLK_n'event and CLK_n = '1' then
			if clk_enable = '1' then
				if MCycle = "001" and TState = "010" and wait_s = '1' then
					Req_Inhibit <= '1';
				else
					Req_Inhibit <= '0';
				end if;
			end if;
        end if;
    end process;

    process (Reset_s,CLK_n)
    begin
        if Reset_s = '0' then
            MReq_Inhibit <= '0';
        elsif CLK_n'event and CLK_n = '0' then
			if clk_falling = '1' then
				if MCycle = "001" and TState = "010" then
					MReq_Inhibit <= '1';
				else
					MReq_Inhibit <= '0';
				end if;
			end if;
        end if;
    end process;

    process (Reset_s,CLK_n)                 -- 0247a
    begin
        if Reset_s = '0' then
            RD <= '0';
            IORQ_n_i <= '1';
            MREQ <= '0';
        elsif CLK_n'event and CLK_n = '0' then
			if clk_falling = '1' then
				if MCycle = "001" then
					if TState = "001" then
						RD <= IntCycle_n;
						MREQ <= IntCycle_n;
						IORQ_n_i <= IntCycle_n;
					end if;
					if TState = "011" then
						RD <= '0';
						IORQ_n_i <= '1';
						MREQ <= '1';
					end if;
					if TState = "100" then
						MREQ <= '0';
					end if;
				else
					if TState = "001" and NoRead = '0' then
						IORQ_n_i <= not IORQ;
						MREQ <= not IORQ;
						if IORQ = '0' then
						  RD <= not Write;
						elsif IORQ_n_i = '0' then
						  RD <= not Write;
						end if;
					end if;
					if TState = "011" then
						RD <= '0';
						IORQ_n_i <= '1';
						MREQ <= '0';
					end if;
				end if;
			end if;
        end if;
    end process;

end;
