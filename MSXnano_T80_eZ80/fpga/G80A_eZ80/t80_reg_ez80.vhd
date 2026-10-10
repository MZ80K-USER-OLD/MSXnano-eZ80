-- Extension fork: Z80 baseline only; ADL not implemented yet.
--
-- T80_eZ80 Registers, technology independent
--
-- Version : 0250_T80 (+k04)
--
-- Copyright (c) 2002 Daniel Wallner (jesus@opencores.org)
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
--  0242 : Initial release
--  0244 : Changed to single register file
--  0250 : Version alignment by KdL 2017.10.23
--
--  +k01 : Version alignment by KdL 2010.10.25
--  +k02 : Version alignment by KdL 2018.05.14
--  +k03 : Version alignment by KdL 2019.05.20
--  +k04 : Separation of T800 from T80_eZ80 by KdL 2021.02.01
--

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity T80_eZ80_Reg is
    port(
        Clk         : in std_logic;
        CEN         : in std_logic;
        RESET_U_n   : in std_logic;
        WEU         : in std_logic;
        DIU         : in std_logic_vector(7 downto 0);
        DOAU        : out std_logic_vector(7 downto 0);
        DOBU        : out std_logic_vector(7 downto 0);
        DOCU        : out std_logic_vector(7 downto 0);
        WEH         : in std_logic;
        WEL         : in std_logic;
        AddrA       : in std_logic_vector(2 downto 0);
        AddrB       : in std_logic_vector(2 downto 0);
        AddrC       : in std_logic_vector(2 downto 0);
        DIH         : in std_logic_vector(7 downto 0);
        DIL         : in std_logic_vector(7 downto 0);
        DOAH        : out std_logic_vector(7 downto 0);
        DOAL        : out std_logic_vector(7 downto 0);
        DOBH        : out std_logic_vector(7 downto 0);
        DOBL        : out std_logic_vector(7 downto 0);
        DOCH        : out std_logic_vector(7 downto 0);
        DOCL        : out std_logic_vector(7 downto 0)
    );
end T80_eZ80_Reg;

architecture rtl of T80_eZ80_Reg is

    type Register_Image is array (natural range <>) of std_logic_vector(7 downto 0);
    signal  RegsU   : Register_Image(0 to 7);
    signal  RegsH   : Register_Image(0 to 7);
    signal  RegsL   : Register_Image(0 to 7);

begin
    -- Slots: BC, DE, HL, IX, BC', DE', HL', IY. AF is separate.
    -- Reset only the new upper storage; original H/L behavior is retained.
    process (Clk, RESET_U_n)
    begin
        if RESET_U_n = '0' then
            RegsU <= (others => (others => '0'));
        elsif rising_edge(Clk) then
            if CEN = '1' and WEU = '1' then
                RegsU(to_integer(unsigned(AddrA))) <= DIU;
            end if;
        end if;
    end process;
    DOAU <= RegsU(to_integer(unsigned(AddrA)));
    DOBU <= RegsU(to_integer(unsigned(AddrB)));
    DOCU <= RegsU(to_integer(unsigned(AddrC)));

    process (Clk)
    begin
        if Clk'event and Clk = '1' then
            if CEN = '1' then
                if WEH = '1' then
                    RegsH(to_integer(unsigned(AddrA))) <= DIH;
                end if;
                if WEL = '1' then
                    RegsL(to_integer(unsigned(AddrA))) <= DIL;
                end if;
            end if;
        end if;
    end process;

    DOAH <= RegsH(to_integer(unsigned(AddrA)));
    DOAL <= RegsL(to_integer(unsigned(AddrA)));
    DOBH <= RegsH(to_integer(unsigned(AddrB)));
    DOBL <= RegsL(to_integer(unsigned(AddrB)));
    DOCH <= RegsH(to_integer(unsigned(AddrC)));
    DOCL <= RegsL(to_integer(unsigned(AddrC)));

end;
