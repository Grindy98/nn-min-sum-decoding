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
    reg [WIDTH_IN - 1 : 0] segm_counter, segm_counter_nxt; // WIDTH_IN bits should be sufficient for the number of variable nodes
    reg [WIDTH_IN - 1 : 0] out_segment, out_segment_nxt;
    reg [N_V - 1 : 0] cw_out, cw_out_nxt;
        
    // state register signal
    reg [2:0] state_reg, state_nxt;
    
    localparam L_SEG = (N_V - 1) / N_LLRS;
    localparam LLR_CHUNK = WIDTH_IN * N_LLRS;
    localparam FIRST_CHUNK = ((N_V - 1) % N_LLRS + 1) * WIDTH_IN;
    
    localparam L_SEG_OUT = (N_V - 1) / WIDTH_OUT;
    localparam FIRST_CHUNK_OUT = (N_V - 1) % WIDTH_OUT + 1;
    
    // states
    localparam IDLE = 3'b000;
    localparam LOAD = 3'b001;
    localparam PROCESS = 3'b010;
    localparam DATA_RDY = 3'b011;
    localparam WRITE_F = 3'b100;
    localparam WRITE = 3'b101;
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
            segm_counter <= 0;
            cw_out <= {100{3'b100}};
        end
        else begin
            state_reg <= state_nxt;  
            
            all_llrs <= all_llrs_nxt;
            segm_counter <= segm_counter_nxt;
            cw_out <= cw_out_nxt;
        end
    end    
    
    always @* begin
        busy = 1'b1; // Always busy unless exceptional state
        data_valid_out = 1'b0; // Unless writing, always on 0
        out_ready = 1'b0;
        state_nxt = state_reg;
        segm_counter_nxt = segm_counter;
        all_llrs_nxt = all_llrs;
        // Drive out bus to Z when unused
        databus_out = {WIDTH_OUT{1'bz}};
        cw_out_nxt = cw_out;
        case(state_reg)
            IDLE     :   begin
                            // Only state in which decoder not busy
                            busy = 0;
                            if(first_data == 1'b1 && data_valid == 1'b1) begin
                                if(segm_counter == L_SEG) begin
                                    // First step and last step are the same
                                    state_nxt = PROCESS;
                                    segm_counter_nxt = 0;
                                end
                                else begin
                                    state_nxt = LOAD;
                                    segm_counter_nxt = segm_counter + 1;
                                end                                
                                all_llrs_nxt[FIRST_CHUNK-1 : 0] = databus_in[FIRST_CHUNK-1 : 0];
                                
                            end
                        end
                      
            LOAD    :   begin
                            if(data_valid == 1'b1) begin
                                if(segm_counter == L_SEG) begin
                                    // Last step of load
                                    state_nxt = PROCESS;
                                    segm_counter_nxt = 0;
                                end
                                else begin
                                    // Continue loading
                                    state_nxt = LOAD;
                                    segm_counter_nxt = segm_counter + 1;
                                end
                                
                                all_llrs_nxt = all_llrs << LLR_CHUNK;
                                all_llrs_nxt[LLR_CHUNK - 1 : 0] = databus_in;
                            end
                        end
            
            PROCESS :   begin
                            state_nxt = DATA_RDY;
                            // to be done 
                        end
            DATA_RDY:   begin
                            out_ready = 1'b1;
                            if(first_data_out == 1'b1) begin
                                state_nxt = WRITE_F;
                            end
                        end 
            WRITE_F :   begin                            
                            // Start write
                            if(segm_counter == L_SEG_OUT) begin
                                // First step and last step are the same
                                state_nxt = RESET;
                                segm_counter_nxt = 0;
                            end
                            else begin
                                state_nxt = WRITE;
                                segm_counter_nxt = segm_counter + 1;
                            end
                            
                            // First element out is padded with 0s for bits not fitting in chunk
                            databus_out = { {WIDTH_OUT-FIRST_CHUNK_OUT{1'b0}}, cw_out[N_V-1 -: FIRST_CHUNK_OUT]};
                            cw_out_nxt = cw_out << FIRST_CHUNK_OUT;
                            data_valid_out = 1;
                        end
            
            WRITE :      begin
                            if(segm_counter == L_SEG_OUT) begin
                                // Last step of writing
                                state_nxt = RESET;
                                segm_counter_nxt = 0;
                            end
                            else begin
                                // Continue writing
                                state_nxt = WRITE;
                                segm_counter_nxt = segm_counter + 1;
                            end
                            databus_out = cw_out[N_V-1 -: WIDTH_OUT];
                            cw_out_nxt = cw_out << WIDTH_OUT;
                            data_valid_out = 1;
                        end
            
            RESET :     begin
                            // Reset everything
                            state_nxt = IDLE;
                            all_llrs_nxt = 0;
                            segm_counter_nxt = 0;
                            cw_out_nxt = {100{3'b100}};
                        end
        endcase
    end
    
endmodule
