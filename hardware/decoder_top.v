`include "ct.vh"

module decoder_top
    #(  parameter WIDTH = 8,
        parameter N_LLRS = 4,
        parameter N_ITER = 5,
        parameter N_V = 31,
        parameter E = 140)
    ( input clk, rst,
      input [N_LLRS * WIDTH - 1 : 0] llr,
      input first_data,
      input data_valid,
      output reg data_ready, 
      
      output reg [N_V - 1 : 0] dw_out,
      output reg first_data_out,
      output reg data_valid_out,
      output reg out_ready);
    
    reg [WIDTH * N_V - 1 : 0] all_llrs, all_llrs_nxt;
    reg [WIDTH - 1 : 0] llr_segment, llr_segment_nxt; // WIDTH bits should be sufficient for the number of variable nodes
    reg [WIDTH - 1 : 0] out_segment, out_segment_nxt;
    reg [N_V - 1 : 0] cw_out;
    reg data_ready_nxt;
   
    wire [WIDTH * E - 1 : 0] proc_elem_i;
    wire ready_last;
    
//    out_layer #(.N_V(N_V), .N_C(N_C), .E(E)) o_layer (  .clk(clk),
//                                                        .rst(rst),
//                                                        .data_ready(data_ready),
//                                                        .prev_ready(ready_last_i),
//                                                        .all_llrs(all_llrs),
//                                                        .prev_proc_elem(proc_elem_i),
//                                                        .dw_out(dw_out),
//                                                        .out_ready(out_ready));     
    
    // sequential logic segment
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            all_llrs <= 0;
            llr_segment <= (N_V - 1) / N_LLRS + 1;
            
            // at first, all_llrs is empty => data is not ready
            data_ready <= 0; 
        end
        else begin
            llr_segment <= llr_segment_nxt;
            
            all_llrs <= all_llrs_nxt;                
            data_ready <= data_ready_nxt;
        end
    end    
    
    // combinational logic segment
    always @* begin
        llr_segment_nxt = llr_segment;
        all_llrs_nxt = all_llrs;
        data_ready_nxt = data_ready;
        
        // at every clock cycle, if data_valid == 1, read the next 4 llrs
        if(data_valid == 1'b1 && !data_ready) begin
            llr_segment_nxt = llr_segment - 1;
                   
            // if all_llrs is full, data_ready should be high
            if(llr_segment > 2) begin
                all_llrs_nxt[N_LLRS * WIDTH - 1 : 0] = llr;
                all_llrs_nxt = all_llrs_nxt << (N_LLRS * WIDTH);
               
            end
            else if(llr_segment == 2) begin
                all_llrs_nxt[N_LLRS * WIDTH - 1 : 0] = llr;
                all_llrs_nxt = all_llrs_nxt << (((N_V - 1) % N_LLRS + 1) * WIDTH);
            end
            else if(llr_segment == 1) begin
                // most significant llrs are ignored
                all_llrs_nxt[N_LLRS * WIDTH - 1 : 0] = all_llrs[N_LLRS * WIDTH - 1 : 0]  | 
                                                        (llr & 
                                                        ~({(WIDTH * N_LLRS){1'b1}} << 
                                                        (((N_V - 1) % N_LLRS + 1) * WIDTH)));
                            
                data_ready_nxt = 1'b1;
            end
        end
    end
    
endmodule
