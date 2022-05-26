`timescale 1ns / 1ps
`define RESET_VAL 1


module out_layer
    #(  parameter WIDTH = 8,
        parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input data_ready,
      input prev_ready,
      input [WIDTH * N_V - 1 : 0] all_llrs,
      input [WIDTH * E - 1 : 0] prev_proc_elem,
      output [N_V - N_C - 1 : 0] dw_out,
      output out_ready);
    
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            // reset logic here
        end
    end
endmodule
