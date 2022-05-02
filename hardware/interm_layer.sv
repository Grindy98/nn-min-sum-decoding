`timescale 1ns / 1ps

// This module represents one iteration (odd + even layer)
module interm_layer
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147,
        parameter N_FP = 8)
    ( input clk, rst,
      input adj_matrix_odd [0:E-1][0:E-1],
      input adj_matrix_even [0:E-1][0:E-1],
      input adj_matrix_in [0:N_V-1][0:E-1],
      input [N_FP-1:0] llr [0:N_V-1],
      input signed [N_FP-1:0] prev_proc_elem [0:E-1],
      output reg signed [N_FP-1:0] proc_elem [0:E-1]);
      
    wire signed [N_FP-1:0] proc_elem_v [0:E-1];
    
    variable_nodes #(.N_V(N_V), .N_C(N_C), .E(E)) v_layer (  .clk(clk),
                                                             .rst(rst),
                                                             .adj_matrix_in(adj_matrix_in),
                                                             .adi_matrix(adj_matrix_odd),
                                                             .llr(llr),
                                                             .prev_proc_elem(prev_proc_elem),
                                                             .proc_elem(proc_elem_v));
    
    check_nodes #(.N_V(N_V), .N_C(N_C), .E(E)) c_layer (  .clk(clk),
                                                          .rst(rst),
                                                          .adj_matrix(adj_matrix_even),
                                                          .prev_proc_elem(proc_elem_v),
                                                          .proc_elem(proc_elem));
endmodule
