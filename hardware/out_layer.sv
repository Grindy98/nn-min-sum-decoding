`timescale 1ns / 1ps

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module out_layer
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input [7:0] tanner_g [0:E-1][0:1],
      input [7:0] llr [0:N_V-1],
      input signed [7:0] prev_proc_elem [0:E-1],
      output reg signed [7:0] out_llr [0:N_V-1] 
    );
    
    reg [7:0] sum = 8'b0;

    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            // do something if reset
        end
    end
    
    always @ (*) begin
        // consider the variable nodes of the Tanner graph
        for(int j = 0; j < N_V; j += 1) begin
            for(int t_i = 0; t_i < E; t_i += 1) begin
                // reinit the sum
                sum <= 0;
                
                // for every check node that composes an edge with the variable node
                if (tanner_g[t_i][0] == j) begin
                    for(int prev_i = 0; prev_i < E; prev_i += 1) begin
                        if ((prev_i == t_i) || (tanner_g[prev_i][0] != j)) begin
                            continue;
                        end
                        
                        sum <= sum + prev_proc_elem[prev_i];
                    end
                end
            end
            
            out_llr[j] <= llr[j] + sum;
        end
    end
    
endmodule
