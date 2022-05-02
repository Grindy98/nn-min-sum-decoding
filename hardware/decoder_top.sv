`timescale 1ns / 1ps

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
module decoder_top 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147,
        parameter N_ITER = 5,
        parameter N_FP = 8)
    ( input clk, rst,
      input [N_V-1:0] cw, // for now consider one codeword as input
      output reg signed [N_FP-1:0] out_llr [0:N_V-1] 
    );
    
    reg signed [N_FP-1:0] in_llr [N_V-1:0];
    reg signed [N_FP-1:0] prev_proc_elem [0:E-1];
    wire signed [N_FP-1:0] proc_elem [0:E-1];
    
    in_to_llr #(.N_V(N_V)) inllr (.clk(clk),
                                  .rst(rst),
                                  .cw(cw),
                                  .llr(in_llr));
         
    interm_layer #(.N_V(N_V), .N_C(N_C), .E(E)) iterm (  .clk(clk),
                                                         .rst(rst),
                                                         .adj_matrix_odd(adj_matrix_odd),
                                                         .adj_matrix_even(adj_matrix_even),
                                                         .adj_matrix_in(adj_matrix_in),
                                                         .prev_proc_elem(prev_proc_elem),
                                                         .proc_elem(proc_elem));
     
    out_layer #(.N_V(N_V), .N_C(N_C), .E(E)) o_layer (  .clk(clk),
                                                        .rst(rst),
                                                        .adj_matrix(adj_matrix_in),
                                                        .llr(in_llr),
                                                        .prev_proc_elem(proc_elem[N_ITER-1]),
                                                        .out_llr(out_llr));                                                          
    
    always @ (posedge clk, negedge rst) begin
        if (!rst) begin
            // For the first iteration, consider the processing elements = 0
            // so initialize prev_proc_elem as such
            for(int i = 0; i < E; i += 1) begin
                prev_proc_elem[i] <= 8'b0;
            end
        end
    end
    
    always @ (posedge clk) begin
        for(int i = 1; i < N_ITER; i += 1) begin
            prev_proc_elem = proc_elem;
        end
    end
    
endmodule
