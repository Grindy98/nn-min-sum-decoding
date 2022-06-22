`include "ct.vh"

module decoder_top
    #(  parameter WIDTH_IN = 8,
        parameter N_LLRS = 4,
        parameter WIDTH_OUT = 8,
        parameter N_ITER = 5,
        parameter N_V = 31,
        parameter E = 140)
    ( input clk, rst,
      input [N_LLRS * WIDTH_IN - 1 : 0] databus_in,
      input first_data,
      input data_valid,

      input first_data_out,
      output reg [WIDTH_OUT-1 : 0] databus_out,
      output reg data_valid_out,
      output reg out_ready,
      
      output reg busy);

    reg [WIDTH_IN * N_V - 1 : 0] all_llrs, all_llrs_nxt;
    reg [WIDTH_IN - 1 : 0] llr_segment, llr_segment_nxt; // WIDTH_IN bits should be sufficient for the number of variable nodes
    reg [WIDTH_IN - 1 : 0] out_segment, out_segment_nxt;
    reg [N_V - 1 : 0] cw_out;
        
    // state register signal
    reg [2:0] state_reg, state_nxt;
    
    localparam L_SEG = (N_V - 1) / N_LLRS;
    localparam LLR_CHUNK = WIDTH_IN * N_LLRS;
    localparam LAST_CHUNK = ((N_V - 1) % N_LLRS + 1) * WIDTH_IN;
    localparam LAST_CHUNK_MASK = ~({LLR_CHUNK{1'b1}} << LAST_CHUNK);
    
    // states
    localparam IDLE = 3'b000;
    localparam LOAD = 3'b001;
    localparam LOAD_L = 3'b010; // load last segment
    localparam PROCESS = 3'b011;
    localparam DATA_RDY = 3'b100;
    localparam OFFLOAD = 3'b101;
    localparam RESET = 3'b111;
    
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
            state_reg <= RESET; // the init state is RESET
            
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
        busy = 1; // Always busy unless exceptional state
        data_valid_out = 0; // Unless writing, always on 0
        state_nxt = state_reg;
        llr_segment_nxt = llr_segment;
        all_llrs_nxt = all_llrs;
        case(state_reg)
            IDLE     :   begin
                            // Only state in which decoder not busy
                            busy = 0;
                            if(first_data == 1'b1 && data_valid == 1'b1) begin
                                // reset the llr segment counter 
                                llr_segment_nxt = 1;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = databus_in;
                                
                                if(llr_segment == L_SEG - 1) begin
                                    state_nxt = LOAD_L;
                                end
                                else begin
                                    state_nxt = LOAD;
                                end
                            end
                        end
                      
            LOAD    :   begin
                            if(data_valid == 1'b1) begin
                                llr_segment_nxt = llr_segment + 1;
                                
                                all_llrs_nxt = all_llrs << LLR_CHUNK;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = databus_in;
                                
                                // keep the state until the second to last segment case is reached
                                state_nxt = (llr_segment == L_SEG - 1) ? LOAD_L : LOAD; 
                            end
                        end
            
            LOAD_L  :   begin
                            if(data_valid == 1'b1) begin
                                llr_segment_nxt = llr_segment + 1;
                                all_llrs_nxt = all_llrs << LAST_CHUNK;
                                
                                // most significant llrs are ignored
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = (all_llrs[LLR_CHUNK - 1 : 0]  << LAST_CHUNK) | 
                                                                        (databus_in & LAST_CHUNK_MASK);
                                state_nxt = PROCESS;   
                            end      
                        end  
                      
            PROCESS :   begin
                            state_nxt = OFFLOAD;
                            // to be done 
                        end
                        
            DATA_RDY :  begin
                            state_nxt = OFFLOAD;
                        end
            
                      
            OFFLOAD :   begin
                            state_nxt = RESET;
                            // to be done
                        end
            RESET :     begin
                            // Reset everything
                            state_nxt = IDLE;
                            all_llrs_nxt = 0;
                            llr_segment_nxt = 0;
                        end
        endcase
    end
    
endmodule
