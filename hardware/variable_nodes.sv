`timescale 1ns / 1ps

// This module is the equivalent of the odd layer (for the
// python model for now)

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module variable_nodes 
    #(  parameter N_V = 44, 
        parameter N_C = 12,
        parameter E = 147,
        parameter N_FP = 8) 
    ( input clk, rst,
      input adj_matrix [0:E-1][0:E-1],
      input adj_matrix_in [0:N_V-1][0:E-1],
      input [N_FP-1:0] llr [0:N_V-1],
      input signed [N_FP-1:0] prev_proc_elem [0:E-1],
      output reg signed [N_FP-1:0] proc_elem [0:E-1]);
    
    always @ (posedge clk, negedge clk) begin
        if (!rst) begin
            for(int i = 0; i < E; i += 1) begin
                proc_elem[i] <= 0;
            end
        end
    end
    
    always @ (*) begin
        // proc_elem = llr + sum(prev connections)
        for(int i = 0; i < E; i += 1) begin
            for(int prev_i = 0; prev_i < N_V; prev_i += 1) begin
                if(adj_matrix_in[prev_i][i] == 1) begin
                    proc_elem[i] = llr[prev_i];
                end
            end
        end
        
        for(int i = 0; i < E; i += 1) begin            
            for(int prev_i = 0; prev_i < E; prev_i += 1) begin
                if(adj_matrix[i][prev_i] == 1) begin
                    proc_elem[i] += prev_proc_elem[prev_i];
                end
            end
        end
    end
    
endmodule
