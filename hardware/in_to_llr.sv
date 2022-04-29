`timescale 1ns / 1ps

module in_to_llr
    #(  parameter N_V = 44,
        parameter LLR = 3)
    ( input clk, rst,
      input [N_V-1:0] cw,
      output reg signed [7:0] llr [0:N_V-1]
    );
    
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            // do something if reset
        end
    end
    
    always @ (*) begin
        for(int i = 0; i < N_V; i += 1) begin
            if (cw[i] == 0) begin
                llr[i] = -1 * LLR;
            end
            else begin
                llr[i] = LLR;
            end
        end
    end 
endmodule
