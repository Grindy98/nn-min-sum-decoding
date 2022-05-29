`timescale 1ns / 1ps
`define RESET_VAL 1

module decoder_top
    #(  parameter WIDTH = 8,
        parameter N_LLRS = 4,
        parameter N_ITER = 5,
        parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147)
    ( input clk, rst,
      input [N_LLRS * WIDTH - 1 : 0] llr,
      input first_data,
      input data_valid,
      output reg data_ready, 
      
      output reg [N_V - N_C - 1 : 0] dw_out,
      output first_data_out,
      output data_valid_out,
      output out_ready);
    
    reg [WIDTH * N_V - 1 : 0] all_llrs;
    reg [WIDTH : 0] llr_segment; // WIDTH bits should be sufficient for the number of variable nodes
   
    wire [WIDTH * E - 1 : 0] proc_elem_i;
    wire ready_last_i;
    
//    out_layer #(.N_V(N_V), .N_C(N_C), .E(E)) o_layer (  .clk(clk),
//                                                        .rst(rst),
//                                                        .data_ready(data_ready),
//                                                        .prev_ready(ready_last_i),
//                                                        .all_llrs(all_llrs),
//                                                        .prev_proc_elem(proc_elem_i),
//                                                        .dw_out(dw_out),
//                                                        .out_ready(out_ready));     
    
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            all_llrs <= 0;
            llr_segment <= 1;
            
            // at first, all_llrs is empty => data is not ready
            data_ready <= 0; 
        end
        else begin
            // at every clock cycle, if data_valid == 1, read the next 4 llrs
            if(data_valid == 1'b1 && !data_ready) begin
                llr_segment <= llr_segment + 1;
                
                // if all_llrs is full, data_ready should be high
                if(llr_segment * N_LLRS < N_V) begin
                    all_llrs[llr_segment * WIDTH * N_LLRS - 1 -: WIDTH * N_LLRS] <= llr;
                
                end
                else begin
                    all_llrs[N_V * WIDTH - 1 -: WIDTH * ((N_V - 1) % N_LLRS + 1)] <= llr[N_LLRS * WIDTH - 1 -: WIDTH * ((N_V - 1) % N_LLRS + 1)];
                    data_ready <= 1'b1;
                end
            end
        end
    end    
    
endmodule
