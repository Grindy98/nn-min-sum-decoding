`timescale 1ns / 1ps

// This modules is the equivalent of the even layer (for the 
// python model for now)

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
// E - number of edges in the Tanner graph
module check_nodes 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147,
        parameter N_FP = 8)
    ( input clk, rst,
      input adj_matrix [0:E-1][0:E-1],
      input signed [N_FP-1:0] prev_proc_elem [0:E-1],
      output reg signed [N_FP-1:0] proc_elem [0:E-1]);
      
    reg [N_FP-1:0] min;
    reg [N_FP-1:0] temp_reg;
    reg signed [1:0] sign_prod;
      
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            min <= 8'b01111111;
            sign_prod <= 2'b01;
            temp_reg <= 8'b0;
            
            for(int i = 0; i < E; i += 1) begin
                proc_elem[i] <= 0;
            end
        end
    end
    
    always @ (*) begin
        for(int i = 0; i < E; i += 1) begin  
            // reinit min, product, temp 
            min = 8'b01111111;
            sign_prod = 2'b01;
            temp_reg = 8'b0;
                     
            for(int prev_i = 0; prev_i < E; prev_i += 1) begin
                if(adj_matrix[i][prev_i] == 1) begin
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
            proc_elem[i] = ((min - 8'b0) < 0) ? 0 : (min - 8'b0);  
            proc_elem[i] *= sign_prod;
        end
    end
endmodule
