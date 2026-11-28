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

-- R24.1: common 24-bit interface; byte storage and reset semantics preserved.
entity T80_Reg_eZ80 is
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
end T80_Reg_eZ80;
architecture rtl of T80_Reg_eZ80 is
    type Register_Image is array (0 to 7) of std_logic_vector(7 downto 0);
    signal RegsH, RegsL, RegsU : Register_Image;
begin
    -- Retain the original reset-free low-byte arrays for RAM inference.
    process(Clk)
    begin
        if rising_edge(Clk) then
            if CEN='1' then
                if WMask(1)='1' then RegsH(to_integer(unsigned(AddrW)))<=DI(15 downto 8);end if;
                if WMask(0)='1' then RegsL(to_integer(unsigned(AddrW)))<=DI(7 downto 0);end if;
            end if;
        end if;
    end process;
    process(RESET_n, Clk)
    begin
        if RESET_n='0' then RegsU<=(others=>(others=>'0'));
        elsif rising_edge(Clk) then
            if CEN='1' then
                -- The existing simultaneous upper-byte exchange is retained.
                if Exchange_U='1' then
                    RegsU(to_integer(unsigned'(Alternate & "10")))<=RegsU(to_integer(unsigned'(Alternate & "01")));
                    RegsU(to_integer(unsigned'(Alternate & "01")))<=RegsU(to_integer(unsigned'(Alternate & "10")));
                end if;
                -- Preserve ordinary-write priority over the exchange.
                if WMask(2)='1' then RegsU(to_integer(unsigned(AddrW)))<=DI(23 downto 16);end if;
            end if;
        end if;
    end process;
    DOA<=RegsU(to_integer(unsigned(AddrA))) & RegsH(to_integer(unsigned(AddrA))) & RegsL(to_integer(unsigned(AddrA)));
    DOB<=RegsU(to_integer(unsigned(AddrB))) & RegsH(to_integer(unsigned(AddrB))) & RegsL(to_integer(unsigned(AddrB)));
    DOC<=RegsU(to_integer(unsigned(AddrC))) & RegsH(to_integer(unsigned(AddrC))) & RegsL(to_integer(unsigned(AddrC)));
    -- One upper-only auxiliary port serves stack/absolute transfer output.
    DOU<=RegsU(to_integer(unsigned(AddrU)));
    views: for i in 0 to 7 generate
        Upper_View(63-i*8 downto 56-i*8)<=RegsU(i);
    end generate;
end;
