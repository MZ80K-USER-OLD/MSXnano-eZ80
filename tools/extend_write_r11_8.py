from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();a=s.index('    -- The legacy writer is unchanged.')
s=s[:a]+'''
    -- R11.8: instruction/width selection is independent of MCycle.
    -- MCycle enters only the final write-cycle product terms. No write
    -- value is repeatedly overridden by the following instruction groups.
    process(Legacy_Write, Write_Class, ISet, MCycle, Ext_Active, Data_Long,
            Stream_Long, ADL_Mode, Has_Width, IntCycle, NMICycle, Branch_Condition)
        variable base_kind, ed_kind : std_logic_vector(3 downto 0);
        variable normal_ext, data_ext, base_set, ed_set, wide, long_data : boolean;
        variable pair_data, absolute_data, pushpop_data, exsp_data, arithmetic_data : boolean;
        variable ed_arithmetic, ea_data, native_control, mixed_control : boolean;
        variable jump_control, alias_guard, return_guard, i16_guard, irq_frame : boolean;
        variable override_legacy, write_data, write_control : boolean;
        variable pair_cycle, absolute_cycle, push_cycle, tail_cycle, pea_cycle, rst_cycle : boolean;
    begin
        base_kind:=Write_Class(3 downto 0);ed_kind:=Write_Class(7 downto 4);
        base_set:=ISet="00";ed_set:=ISet="10";
        normal_ext:=Ext_Active='1' and IntCycle='0' and NMICycle='0';
        data_ext:=normal_ext and Mode=0;
        wide:=Data_Long='1' or Stream_Long='1';long_data:=Data_Long='1';

        -- All ownership/override predicates depend only on held instruction
        -- state, widths, and interrupt state, never on the current MCycle.
        pair_data:=data_ext and wide and
            ((base_set and (base_kind=x"1" or base_kind=x"2")) or
             (ed_set and (ed_kind=x"1" or ed_kind=x"2")));
        absolute_data:=data_ext and wide and base_set and (base_kind=x"3" or base_kind=x"4");
        pushpop_data:=data_ext and long_data and base_set and (base_kind=x"5" or base_kind=x"6");
        exsp_data:=data_ext and long_data and base_set and base_kind=x"7";
        arithmetic_data:=data_ext and long_data and base_set and base_kind=x"8";
        ed_arithmetic:=data_ext and long_data and ed_set and ed_kind=x"3";
        ea_data:=data_ext and ed_set and (ed_kind=x"4" or ed_kind=x"5" or ed_kind=x"6");
        jump_control:=normal_ext and base_set and base_kind=x"9" and Data_Long=Stream_Long;
        native_control:=normal_ext and ADL_Mode='1' and Has_Width='0' and base_set and
            (base_kind=x"A" or base_kind=x"B" or base_kind=x"C" or base_kind=x"D" or base_kind=x"E");
        mixed_control:=Ext_Active='1' and Has_Width='1' and base_set and
            (base_kind=x"A" or base_kind=x"B" or base_kind=x"C" or base_kind=x"D" or base_kind=x"E");
        alias_guard:=ADL_Mode='1' and ed_set and ed_kind=x"7";
        return_guard:=normal_ext and ed_set and ed_kind=x"8" and (ADL_Mode='1' or Has_Width='1');
        i16_guard:=normal_ext and ed_set and ed_kind=x"9";
        irq_frame:=Ext_Active='1' and ADL_Mode='1' and (IntCycle='1' or NMICycle='1');
        override_legacy:=pair_data or absolute_data or pushpop_data or exsp_data or arithmetic_data or
            ed_arithmetic or ea_data or jump_control or native_control or mixed_control or
            alias_guard or return_guard or i16_guard or irq_frame;

        -- Shared, explicit 3-bit cycle predicates; no integer comparison or
        -- variable last-address arithmetic lies on the MCycle path.
        pair_cycle:=MCycle(2)='1' and (Stream_Long='0' or MCycle(1)='1' or MCycle(0)='1');
        absolute_cycle:=MCycle(2)='1' and MCycle(1)='0' and MCycle(0)=Stream_Long;
        push_cycle:=(MCycle(2)='0' and MCycle(1)='1') or MCycle="100";
        tail_cycle:=MCycle(2)='1' and (MCycle(1)='1' or MCycle(0)='1');
        pea_cycle:=MCycle(2)='1' or (MCycle(1)='1' and MCycle(0)='1');
        rst_cycle:=MCycle(2)='1' or MCycle(1)='1';

        write_data:=(pair_data and pair_cycle and
                       ((base_set and base_kind=x"1") or (ed_set and ed_kind=x"1"))) or
                    (absolute_data and base_kind=x"3" and absolute_cycle) or
                    (pushpop_data and base_kind=x"5" and push_cycle) or
                    (exsp_data and tail_cycle) or
                    (ea_data and ed_kind=x"6" and pea_cycle);
        write_control:=(native_control and tail_cycle and
                         (base_kind=x"A" or (base_kind=x"B" and Branch_Condition='1'))) or
                       (native_control and base_kind=x"E" and rst_cycle) or
                       (irq_frame and push_cycle);
        -- IRQ entry supersedes mixed/alias guards; other write-producing
        -- classes are disjoint and require IntCycle=NMICycle=0.
        if (Legacy_Write='1' and not override_legacy) or write_data or write_control then
            Write<='1';
        else
            Write<='0';
        end if;
    end process;

end;
''';p.write_text(s)
