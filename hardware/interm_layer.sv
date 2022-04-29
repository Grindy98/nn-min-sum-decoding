`timescale 1ns / 1ps

// This module represents one iteration (odd + even layer)
module interm_layer
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input [7:0] tanner_g [0:E-1][0:1],
      input [7:0] llr [0:N_V-1],
      input signed [7:0] prev_proc_elem [0:E-1],
      output reg signed [7:0] proc_elem [0:E-1]);
      
    wire signed [7:0] proc_elem_v [0:E-1];
    
    variable_nodes #(.N_V(N_V), .N_C(N_C), .E(147)) v_layer (  .clk(clk),
                                                               .rst(rst),
                                                               .tanner_g(tanner_g),
                                                               .llr(llr),
                                                               .prev_proc_elem(prev_proc_elem),
                                                               .proc_elem(proc_elem_v));
    
    check_nodes #(.N_V(N_V), .N_C(N_C), .E(147)) c_layer (  .clk(clk),
                                                            .rst(rst),
                                                            .tanner_g(tanner_g),
                                                            .prev_proc_elem(proc_elem_v),
                                                            .proc_elem(proc_elem));
endmodule
