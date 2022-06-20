`timescale 1ns / 1ps
`define RESET_VAL 1

module decoder_top_test
    #(  parameter WIDTH = 8,
        parameter N_LLRS = 4,
        parameter N_ITER = 5,
        parameter N_V = 31,
        parameter E = 140)
    ( input clk, rst,
      input [N_LLRS * WIDTH - 1 : 0] llr,
      input first_data,
      input data_valid,
     
      output reg [N_V - 1 : 0] dw_out,
      output reg first_data_out,
      output reg data_valid_out,
      output reg out_ready);
    
    reg [WIDTH * N_V - 1 : 0] all_llrs, all_llrs_nxt;
    reg [WIDTH - 1 : 0] llr_segment, llr_segment_nxt; // WIDTH bits should be sufficient for the number of variable nodes
    reg [WIDTH - 1 : 0] out_segment, out_segment_nxt;
    reg [N_V - 1 : 0] cw_out;
    
    // state register signal
    reg [2:0] state_reg, state_nxt;
    
    localparam STL_SEG = (N_V - 1) / N_LLRS - 1;
    localparam LLR_CHUNK = WIDTH * N_LLRS;
    localparam LAST_CHUNK = ((N_V - 1) % N_LLRS + 1) * WIDTH;
    localparam LAST_CHUNK_MASK = ~({LLR_CHUNK{1'b1}} << LAST_CHUNK);
    
    // states
    localparam IDLE = 3'b000;
    localparam LOAD = 3'b001;
    localparam LOAD_STL = 3'b010; // load second to last segment
    localparam LOAD_L = 3'b011; // load last segment
    localparam PROCESS = 3'b100;
    localparam OFFLOAD = 3'b101;
    
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
            state_reg <= IDLE; // the init state is IDLE
            
            all_llrs <= 0;
            llr_segment <= 0;
        end
        else begin
            state_reg <= state_nxt;  
            llr_segment <= llr_segment_nxt;
            
            all_llrs <= all_llrs_nxt;
        end
    end    
    
    always @* begin
        state_nxt = state_reg;
        llr_segment_nxt = llr_segment;
        all_llrs_nxt = all_llrs;
        
        case(state_reg)
            IDLE     :   begin
                            if(first_data == 1'b1 && data_valid == 1'b1) begin
                                // reset the llr segment counter 
                                llr_segment_nxt = 1;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = llr;
                                
                                state_nxt = LOAD;
                            end
                        end
                      
            LOAD    :   begin
                            if(data_valid == 1'b1) begin
                                llr_segment_nxt = llr_segment + 1;
                                
                                all_llrs_nxt = all_llrs << LLR_CHUNK;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = llr;
                                
                                // keep the state until the second to last segment case is reached
                                state_nxt = (llr_segment == (STL_SEG - 1)) ? LOAD_STL : LOAD; 
                            end
                        end
                        
            LOAD_STL:   begin
                            if(data_valid == 1'b1) begin
                                llr_segment_nxt = llr_segment + 1;
                                
                                all_llrs_nxt = all_llrs << LLR_CHUNK;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = llr;
                                
                                state_nxt = LOAD_L;
                            end
                        end
            
            LOAD_L  :   begin
                            if(data_valid == 1'b1) begin
                                llr_segment_nxt = llr_segment + 1;
                                all_llrs_nxt = all_llrs << LAST_CHUNK;
                                
                                // most significant llrs are ignored
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = (all_llrs[LLR_CHUNK - 1 : 0]  << LAST_CHUNK) | 
                                                                        (llr & LAST_CHUNK_MASK);
                                state_nxt = PROCESS;    
                            end      
                        end  
                      
            PROCESS :   begin
                            state_nxt = OFFLOAD;
                            // to be done 
                        end
                      
            OFFLOAD :   begin
                            state_nxt = IDLE;
                            // to be done
                        end
        endcase
    end
    
endmodule
