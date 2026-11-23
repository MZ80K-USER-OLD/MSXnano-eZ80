# Shared settings for both profiles; paths are relative to this script.
# GOWIN execution is required; this file does not launch synthesis itself.
set r245_fpga_dir [file dirname [file normalize [info script]]]
proc configure_uart_profile {profile} {
    global r245_fpga_dir
    switch -- $profile {
        normal {
            set r245_project [file join $r245_fpga_dir project_eZ80 MSXNanoTang20K_eZ80.gprj]
        }
        diagnostic {
            set r245_project [file join $r245_fpga_dir project_eZ80_uart_debug MSXNanoTang20K_eZ80_UART_DEBUG.gprj]
        }
        default {error "Expected normal or diagnostic"}
    }
    open_project $r245_project
    set_option -top_module top
    set_option -verilog_std sysv2017
    set_option -vhdl_std vhd1993
    set_option -include_path [file join $r245_fpga_dir src]
    set_option -looplimit 2000
    set_option -maxfan 1000
    set_option -rw_check_on_ram 0
    set_option -place_option 0
    set_option -route_option 0
    # Same dual-purpose-pin choices as the hardware-tested 95% build.
    set_option -use_mspi_as_gpio 1
    set_option -use_sspi_as_gpio 1
    set_option -use_jtag_as_gpio 0
    puts "R24.5 UART profile: $profile"
    puts "Project: $r245_project"
}
