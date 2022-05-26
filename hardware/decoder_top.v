`timescale 1ns / 1ps
`define RESET_VAL 1

module decoder_top
    #(  parameter WIDTH = 8,
        parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input data_valid,
      input [4 * WIDTH : 0] llr,
      output [N_V - N_C - 1 : 0] dw_out,
      output out_ready);
    
    reg [WIDTH * N_V - 1 : 0] all_llrs;
    reg data_ready;
   
    wire [WIDTH * E - 1 : 0] proc_elem_i;
    wire ready_last_i;
    
    out_layer #(.N_V(N_V), .N_C(N_C), .E(E)) o_layer (  .clk(clk),
                                                        .rst(rst),
                                                        .data_ready(data_ready),
                                                        .prev_ready(ready_last_i),
                                                        .all_llrs(all_llrs),
                                                        .prev_proc_elem(proc_elem_i),
                                                        .dw_out(dw_out),
                                                        .out_ready(out_ready));     
    
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            // reset logic here
        end
    end
endmodule
