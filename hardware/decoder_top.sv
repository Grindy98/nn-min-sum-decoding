`include "ct.vh"

module decoder_top
    #(  
        parameter LLR_WIDTH=`LLR_WIDTH,
        parameter EXTENDED_BITS=`EXTENDED_BITS,
        parameter N_ITER=`N_ITER,
        parameter N_V=`N_V,
        parameter E=`E
    )( 
        input clk, 
        input rst,
        axi_stream_if.slave from_env,
        axi_stream_if.master to_env
    );

    // ARRAY SIZES
    localparam INP_ARR_SIZE = LLR_WIDTH * N_V;
    localparam OUT_ARR_SIZE = N_V;
    localparam INP_ITER_N = (INP_ARR_SIZE-1) / from_env.WIDTH + 1;
    localparam OUT_ITER_N = (OUT_ARR_SIZE-1) / to_env.WIDTH + 1;
    localparam WRITE_PAD = (OUT_ARR_SIZE-1) % to_env.WIDTH + 1;

    // All-purpose counter
    reg [`INT_SIZE - 1 : 0] segm_counter, segm_counter_nxt;
    
    // Input reg that stores all llrs after a successful read
    reg [INP_ARR_SIZE - 1 : 0] all_llrs, all_llrs_nxt;
    // Output reg that stores a valid codeword after decoding for transmission
    reg [OUT_ARR_SIZE - 1 : 0] cw_out, cw_out_nxt;
    //reg [ - 1 : 0] out_segment, out_segment_nxt;
    wire [OUT_ARR_SIZE - 1 : 0] cw_result;
    
    // Inverted input and output for processing
    wire [INP_ARR_SIZE - 1 : 0] all_llrs_inverted;
    wire [OUT_ARR_SIZE - 1 : 0] cw_result_inverted;
    
    // Intermediary reg storing NN results between iterations
    reg [LLR_WIDTH * E - 1 : 0] layer_inp_llr, layer_inp_llr_nxt;
    wire [LLR_WIDTH * E - 1 : 0] layer_out_llr;
        
    // state register signal
    reg [2:0] state_reg, state_nxt;
    
    // STATES
    localparam RESET = 3'b000;
    localparam READ = 3'b001;
    localparam PROCESS = 3'b010;
    localparam WRITE = 3'b011;
    
    interm_layer #(
        .WIDTH(LLR_WIDTH),
        .N_V(N_V),
        .E(E),
        .EXTENDED_BITS(EXTENDED_BITS)
    )layer(
        .bias_idx(segm_counter),
        .all_llrs(all_llrs_inverted),
        .prev_proc_elem(layer_inp_llr),
        .proc_elem(layer_out_llr)
    );
    
    out_layer #(
        .WIDTH(LLR_WIDTH),
        .N_V(N_V),
        .E(E),
        .EXTENDED_BITS(EXTENDED_BITS)
        )o_layer(
            .all_llrs(all_llrs_inverted),
            .prev_proc_elem(layer_out_llr),
            .cw_out(cw_result)
        );
    
    // Assign inverted wires
    assign all_llrs_inverted = {<<`LLR_WIDTH{all_llrs}};
    assign cw_result_inverted = {<<{cw_result}};

    // sequential logic segment
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            state_reg <= RESET; // the init state is RESET
            
            // Internal
            all_llrs <= 0;
            segm_counter <= 0;
            cw_out <= 0;
            layer_inp_llr <= 0;
        end
        else begin
            state_reg <= state_nxt;  
            
            // Internal
            all_llrs <= all_llrs_nxt;
            segm_counter <= segm_counter_nxt;
            cw_out <= cw_out_nxt;
            layer_inp_llr <= layer_inp_llr_nxt;
        end
    end    
    
    always @* begin
        // DEFAULT OUTPUTS
        state_nxt = state_reg;

        // Interface
        from_env.tready = 0;

        to_env.tvalid = 0;
        to_env.tlast = 0;
    	to_env.tdata = {to_env.WIDTH{1'bz}};

        // Internal
        all_llrs_nxt = all_llrs;
        segm_counter_nxt = segm_counter;
        cw_out_nxt = cw_out;
        layer_inp_llr_nxt = layer_inp_llr;

        case(state_reg)
            RESET: begin
                state_nxt = READ;
            end
            READ: begin
                from_env.tready = 1'b1;
                // Check if databus valid
                if(from_env.tvalid) begin
                    // Read the input
                    all_llrs_nxt = {all_llrs, from_env.tdata};
                    if(segm_counter == INP_ITER_N-1) begin
                        // Final iteration
                        state_nxt = PROCESS;
                        segm_counter_nxt = 0;
                    end else begin
                        // Increment iteration
                        segm_counter_nxt = segm_counter + 1;
                    end
                end
                // Otherwise the bus is not read, wait until valid
            end
            WRITE: begin
                // Put next output on bus regardless of 
                to_env.tvalid = 1'b1;
                // Check if first iteration
                if(segm_counter == 0) begin
                    // First write
                    to_env.tdata = 0;
                    to_env.tdata = cw_out[OUT_ARR_SIZE-1 -: WRITE_PAD];
                end else begin
                    // Normal write
                    to_env.tdata = cw_out[OUT_ARR_SIZE-1 -: to_env.WIDTH];
                end
                // Check if ready
                if(to_env.tready) begin
                    // Only move the codeword forward if ready for write
                    cw_out_nxt = cw_out << ((segm_counter == 0) ? WRITE_PAD : to_env.WIDTH);
                    if(segm_counter == OUT_ITER_N-1) begin
                        // Final iteration
                        state_nxt = READ;
                        segm_counter_nxt = 0;
                        to_env.tlast = 1'b1;
                    end else begin
                        // Increment iteration
                        segm_counter_nxt = segm_counter + 1;
                    end
                end
                // Otherwise the bus is not written, wait until ready
            end   
            PROCESS: begin
                segm_counter_nxt = segm_counter + 1;
                layer_inp_llr_nxt = layer_out_llr;
                if(segm_counter == N_ITER-1) begin
                    // End processing
                    state_nxt = WRITE;
                    segm_counter_nxt = 0;
                    all_llrs_nxt = 0;
                    layer_inp_llr_nxt = 0;
                    // Save output
                    cw_out_nxt = cw_result_inverted;
                end
            end   
        endcase

    end

endmodule
