`timescale 1ns / 1ps

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module out_layer
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147,
        parameter N_FP = 8)
    ( input clk, rst,
      input adj_matrix [0:N_V-1][0:E-1],
      input signed [N_FP-1:0] llr [0:N_V-1],
      input signed [N_FP-1:0] prev_proc_elem [0:E-1],
      output reg signed [N_FP-1:0] out_llr [0:N_V-1] 
    );
    
    always @ (*) begin
        for(int prev_i = 0; prev_i < N_V; prev_i += 1) begin
                out_llr[prev_i] = llr[prev_i];
        end
        
        for(int i = 0; i < N_V; i += 1) begin            
            for(int prev_i = 0; prev_i < E; prev_i += 1) begin
                if(adj_matrix[i][prev_i] == 1) begin
                    out_llr[i] += prev_proc_elem[prev_i];
                end
            end
        end
    end
endmodule
