`timescale 1ns / 1ps
`define RESET_VAL 1

// Odd layer
module variable_nodes
    #(  parameter WIDTH = 8,
        parameter N_V = 44,
        parameter E = 147)
    ( input clk, rst,
      input data_ready,
      input prev_ready,
      input [WIDTH * N_V - 1 : 0] all_llrs,
      input [WIDTH * E - 1 : 0] prev_proc_elem,
      output [WIDTH * E - 1 : 0] proc_elem,
      output varn_ready);
    
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            // reset logic here
        end
    end
endmodule
