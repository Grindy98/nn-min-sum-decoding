`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11.06.2022 16:08:19
// Design Name: 
// Module Name: tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

interface decoder_interface
    #(  parameter WIDTH_IN = 8,
        parameter N_LLRS = 4,
        parameter WIDTH_OUT = 8,
        parameter N_ITER = 5,
        parameter N_V = 31,
        parameter E = 140)
    ( input clk, rst);
      logic [N_LLRS * WIDTH_IN - 1 : 0] databus_in;
      logic [WIDTH_OUT - 1 : 0] databus_out;
      
      logic first_data;
      logic data_valid;
      
      logic first_data_out;
      logic [N_V - 1 : 0] dw_out;
      logic data_valid_out;
      logic out_ready;
      
      logic busy;
endinterface

class cw_wrapper #(
    parameter N_V,
    parameter LLR_SIZE);
    logic[N_V-1:0][LLR_SIZE-1:0] cw ;
endclass

module tb();

import "DPI-C" function void before_start(); 
import "DPI-C" function void before_end(); 

import "DPI-C" function void pass_through_model(input int cw[], output logic outpArrHandle[]);
import "DPI-C" function int generate_noisy_cw(output int cw[], input real cross_p, input int n_errors);

export "DPI-C" function c_print_wrapper;

function void c_print_wrapper(input string to_print);
    $display("[C] %s", to_print);
endfunction

localparam LLR_SIZE = 8;
localparam N_V = 15;
localparam N_V_HW = N_V;
localparam WIDTH_OUT = LLR_SIZE;
localparam E = 38;
localparam cross_p = 0.01;

reg clk;
reg rst;

decoder_interface #(
    .WIDTH_IN(LLR_SIZE),
    .WIDTH_OUT(WIDTH_OUT),
    .N_V(N_V_HW),
    .E(E)
)dut_i(
    .clk(clk),
    .rst(rst)
);

decoder_top #(
    .WIDTH_IN(dut_i.WIDTH_IN),
    .WIDTH_OUT(dut_i.WIDTH_OUT),
    .N_LLRS(dut_i.N_LLRS),
    .N_ITER(dut_i.N_ITER),
    .N_V(dut_i.N_V),
    .E(dut_i.E)
) dut (
    .clk(dut_i.clk),
    .rst(dut_i.rst),
    .databus_in(dut_i.databus_in),
    .first_data(dut_i.first_data),
    .data_valid(dut_i.data_valid),
    .busy(dut_i.busy),
    .first_data_out(dut_i.first_data_out),
    .databus_out(dut_i.databus_out),
    .data_valid_out(dut_i.data_valid_out),
    .out_ready(dut_i.out_ready)
);

initial begin
    clk = 0;
    forever #50 clk = ~clk;
end

initial begin
    rst = 1;
    // Initialize input data of interface
    dut_i.data_valid = 0;
    dut_i.first_data = 0;
    dut_i.databus_in = 0;
    #200 rst = 0;
end



mailbox gen_to_dut = new(2);
mailbox dut_to_chk = new(2);
mailbox gen_to_chk = new(2);

task generate_cw;
    
//	call c function generate_cw, apply_channel 
	
//	put in mailbox (input)

//	generate signals with c outputs
    int flag;
    int i; 
    automatic cw_wrapper #(
        .N_V(dut_i.N_V),
        .LLR_SIZE(dut_i.WIDTH_IN)
    ) w;
    int generated_cw[N_V-1:0];
    logic passed_cw [N_V-1:0];
    logic [N_V-1:0] passed_cw_packed;
    logic [LLR_SIZE-1:0] cw_bit [N_V];
    
    forever begin
        #500 $display("Generating signal");
        
        flag = generate_noisy_cw(generated_cw, cross_p, 1);
        
        if(flag == 1) begin
            $display("Metaparameters don't match");
        end
        
        w = new();
        for (i=0; i<dut_i.N_V; i=i+1) begin
            w.cw[i] = generated_cw[i];
        end
        // Send to dut
        gen_to_dut.put(w);
        // Get output from C model and send for checking
        pass_through_model(generated_cw, passed_cw);
        passed_cw_packed = {>>1{passed_cw}};
        gen_to_chk.put(passed_cw_packed);
        
    end 
endtask 

logic[N_V_HW-1:0][LLR_SIZE-1:0] debug_driver_input;

task drive_dut;
    automatic cw_wrapper #(
        .N_V(dut_i.N_V),
        .LLR_SIZE(dut_i.WIDTH_IN)
    ) w;
    automatic bit is_writing = 0;
    automatic int llr_index = -1;
    forever begin
        @(negedge clk);
        dut_i.data_valid = 0;
        if(is_writing == 0) begin
            // If device busy but not writing, skip cycle
            if(dut_i.busy == 1) begin
                continue;
            end
            // If no message, skip cycle
            if(gen_to_dut.try_get(w) == 0) begin
                continue;
            end
            else begin
                is_writing = 1;
                llr_index = dut_i.N_V-1;
            end
            debug_driver_input = w.cw;
        end
        // We reach this point only if we currently have to write
        
        // Initialize various ports of interface
        dut_i.databus_in = 0;
        dut_i.first_data = 0;
        if(llr_index == dut_i.N_V-1) begin
            dut_i.first_data = 1;
        end
        forever begin
            dut_i.databus_in = dut_i.databus_in << dut_i.WIDTH_IN;
            dut_i.databus_in[dut_i.WIDTH_IN-1 : 0] = w.cw[llr_index];
            llr_index -= 1;
            // If index is divisible by chunk size, break
            if((llr_index + 1) % dut_i.N_LLRS == 0) begin
                break;
            end
        end
        // Check for end
        if(llr_index == -1) begin
            is_writing = 0;
        end
        // LLR chunk ready to be sent
        dut_i.data_valid = 1;
    end
endtask

logic [dut_i.N_V-1 : 0] debug_read_bits;

task monitor_dut;
//	extract signals 
	
//	put in mailbox (output) 
    automatic bit is_reading = 0;
    automatic logic [dut_i.N_V-1 : 0] read_bits;
    forever begin
        @(negedge clk);
        // Drive first data signal to low unless writing
        if(is_reading == 0) begin
            dut_i.first_data_out = 0;
            if(dut_i.out_ready == 1) begin
                dut_i.first_data_out = 1;
                is_reading = 1;
            end
            continue;
        end
        // Reading starts
        if(dut_i.data_valid_out == 0) begin
            // End of read
            is_reading = 0;
            dut_to_chk.put(read_bits);
            continue;
        end
        
        // Shift register and read
        read_bits = read_bits << dut_i.WIDTH_OUT;
        read_bits[dut_i.WIDTH_OUT-1 : 0] = dut_i.databus_out;
        debug_read_bits = read_bits;
    end 
endtask

logic [N_V-1:0] out_passed_cw;

task check_cw; 
//	mailbox.get (input)
//	mailbox.get(output)
	
//	call c function input
    automatic logic [N_V-1:0] cw_out_c;
    automatic logic [dut_i.N_V-1:0] cw_out_dut;
    forever begin
        gen_to_chk.get(cw_out_c);
        dut_to_chk.get(cw_out_dut);
        $display("Receiving resulting signals");
        $displayb(cw_out_c);
        $displayb(cw_out_dut);
    end 
endtask 

initial begin
    before_start();
    fork
        generate_cw();
        drive_dut();
        monitor_dut();
        check_cw();
    join
    before_end();
end

endmodule
