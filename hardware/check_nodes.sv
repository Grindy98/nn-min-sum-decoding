`timescale 1ns / 1ps

//////////////////////////////////////////////////////////////////////////////////
// Module Name: check_nodes
//
// Revision 0.01 - File Created
// Additional Comments: This modules is the equivalent of the even layer (for the 
// python model for now)
// 
//////////////////////////////////////////////////////////////////////////////////

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module check_nodes 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input h_matrix [0:N_C-1][0:N_V-1],
      input signed [7:0] prev_proc_elem [0:E-1],
      output reg signed [7:0] proc_elem [0:E-1]);
      
    reg [7:0] sum = 8'b0;
    reg [7:0] min = 8'b11111111;
    reg signed [1:0] sign_prod = 2'b00;
      
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            // do something if reset
        end
    end
    
    always @ (*) begin
        // consider the check nodes of the Tanner graph
        for(int i = 0; i < N_C; i += 1) begin
            for(int j = 0; j < N_V; j += 1) begin
                // for every edge
                if (h_matrix[i][j] == 1) begin
                    for(int prev_j = 0; prev_j < N_V; prev_j += 1) begin
                        if (prev_j == j) begin
                            continue;
                        end
                     
                        // TODO: implement min module
                        // find the min value for processing elem
                        min <= (min >  prev_proc_elem[prev_j + i * N_C])? min : prev_proc_elem[prev_j + i * N_C];
                        
                        // todo: implement sign module, this is not correct
                        sign_prod <= sign_prod * ((prev_proc_elem[prev_j + i * N_C] > 0)? 1 : -1);
                    end
                    
                    // TODO: implement max module
                    // for now the coeficients are hardcoded
                    proc_elem[i * N_C + j] <= ((min - 8'b0) < 0) ? 0 : (min - 8'b0);  
                    proc_elem[i * N_C + j] <= proc_elem[i * N_C + j] * sign_prod;
                end
            end
        end
    end
endmodule
