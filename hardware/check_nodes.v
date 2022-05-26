`timescale 1ns / 1ps
`define RESET_VAL 1

// Even layer
module check_nodes 
    #(  parameter WIDTH = 8,
        parameter E = 147)
    ( input clk, rst,
      input prev_ready,
      input [WIDTH * E - 1 : 0] prev_proc_elem,
      output [WIDTH * E - 1 : 0] proc_elem,
      output checkn_ready);
    
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            // reset logic here
        end
    end
endmodule
