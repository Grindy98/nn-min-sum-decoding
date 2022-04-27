`timescale 1ns / 1ps

//////////////////////////////////////////////////////////////////////////////////
// Module Name: variable_nodes
// 
// Revision 0.01 - File Created
// Additional Comments: This module is the equivalent of the odd layer (for the
// python model for now)
// 
//////////////////////////////////////////////////////////////////////////////////

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module variable_nodes 
    #(  parameter N_V = 44, 
        parameter N_C = 12,
        parameter E = 147) 
    ( input clk, rst,
      input h_matrix [0:N_C-1][0:N_V-1],
      input [7:0] llr [0:N_V-1],
      input signed [7:0] prev_proc_elem [0:E-1],
      output reg signed [7:0] proc_elem [0:E-1]);
      
    reg [7:0] sum = 8'b0;
      
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            // do something if reset
        end
    end
    
    always @ (*) begin
        // consider the variable nodes of the Tanner graph
        for(int j = 0; j < N_V; j += 1) begin
            for(int i = 0; i < N_C; i += 1) begin
                // for every edge
                if (h_matrix[i][j] == 1) begin
                    for(int prev_i = 0; prev_i < N_C; prev_i += 1) begin
                        if (prev_i == i) begin
                            continue;
                        end
                        
                        sum <= sum + prev_proc_elem[j + prev_i * N_C];
                    end
                    
                    proc_elem[j + i * N_C] <= llr[j] + sum;
                end
            end
        end
    end
    
endmodule
