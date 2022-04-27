`timescale 1ns / 1ps

//////////////////////////////////////////////////////////////////////////////////
// Module Name: decoder_top
//
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
module decoder_top 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter N_ITER = 5)
    ( input clk, rst
    );
    
    // if it is the first iteration, consider the processing elements = 0
    
    // read the H matrix from a file perhaps
    reg h_matrix [0:N_C-1][0:N_V-1];
endmodule
