    always @(posedge clk_27m) begin
        if (~bus_reset_n) begin
            config_mapper_slot_ff <= config1_ff[5:4];
            //config_megaram_slot_ff <= config1_ff[7:6];
            config_enable_mapper3 <= (config1_ff[0] == 1 && config1_ff[5:4] == 2'b11);
            config_enable_mapper12 <= (config1_ff[0] == 1 && config1_ff[5:4] != 2'b11);
            config_enable_sdcard <= config2_ff[0];
            config_sdcard_slot_ff <= config2_ff[2:1];
        end
    end
