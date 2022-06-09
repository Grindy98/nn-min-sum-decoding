`timescale 1ns / 1ps
`define RESET_VAL 1

module check_nodes
	#(  parameter WIDTH = 8,
	    parameter N_V = 31,
	    parameter E = 140)
	( input clk, rst,
	  input data_ready,
	  input prev_ready,
	  input [WIDTH * N_V - 1 : 0] all_llrs,
	  input [WIDTH * E - 1 : 0] prev_proc_elem,
	  output reg [WIDTH * E - 1 : 0] proc_elem,
	  output reg varn_ready);

endmodule
