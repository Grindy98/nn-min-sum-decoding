`timescale 1ns / 1ps

// This modules is the equivalent of the even layer (for the 
// python model for now)

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module check_nodes 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input [7:0] tanner_g [0:E-1][0:1],
      input signed [7:0] prev_proc_elem [0:E-1],
      output reg signed [7:0] proc_elem [0:E-1]);
      
    reg [7:0] sum;
    reg [7:0] min;
    reg signed [1:0] sign_prod;
    reg [7:0] temp_reg;
      
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            sum = 8'b0;
            min = 8'b01111111;
            sign_prod = 2'b00;
            temp_reg = 8'b0;
        end
    end
    
    always @ (*) begin
        // consider the variable nodes of the Tanner graph
        for(int i = 0; i < N_C; i += 1) begin
            for(int t_i = 0; t_i < E; t_i += 1) begin
                // reinit the sum, product and min
                temp_reg = 8'b0;
                sum = 0;
                sign_prod = 1;
                min = 8'b01111111;
                
                // for every variable node that composes an edge with the check node
                if (tanner_g[t_i][1] == i) begin
                    for(int prev_i = 0; prev_i < E; prev_i += 1) begin
                        if ((prev_i == t_i) || (tanner_g[prev_i][1] != i)) begin
                            continue;
                        end
                        
                        // find the min value for processing elem
                        temp_reg = prev_proc_elem[prev_i];
                        min = (min > temp_reg)? min : temp_reg;
                        
                        // The value of the sign_prod changes only in the case 
                        // that temp_reg is either negative or zero
                        // If temp_reg is positive, the product multiplied by 1 
                        // is that product
                        if (temp_reg < 0) begin 
                            sign_prod = sign_prod * (-1);
                        end
                        else if (temp_reg == 0) begin
                            // sign(0) = 0
                            sign_prod = 0;
                        end
                    end    
                end
                
                // for now the coeficients are hardcoded
                proc_elem[t_i] = ((min - 8'b0) < 0) ? 0 : (min - 8'b0);  
                proc_elem[t_i] = proc_elem[t_i] * sign_prod;
            end
        end
    end
endmodule
