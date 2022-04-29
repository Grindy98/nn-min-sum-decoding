`timescale 1ns / 1ps

// N_V - number of variable nodes in the Tanner graph
// N_C - number of check nodes in the Tanner graph
module decoder_top 
    #(  parameter N_V = 44,
        parameter N_C = 12,
        parameter E = 147,
        parameter N_ITER = 5,
        parameter H_MATRIX_FILE = "h_44_32.mem")
    ( input clk, rst,
      input [N_V-1:0] cw, // for now consider one codeword as input
      output reg signed [7:0] out_llr [0:N_V-1] 
    );
    
    // read the H matrix from a file perhaps
    reg [N_V-1:0] h_matrix [0:N_C-1];
    reg [7:0] tanner_g [0:E-1][0:1];
    reg signed [7:0] in_llr [N_V-1:0];
    
    reg signed [7:0] proc_l1 [0:E-1];
    wire signed [7:0] proc_elem [0:N_ITER-1][0:E-1];
    
    generate
        if (H_MATRIX_FILE != "") begin: use_init_file
            initial 
                $readmemb(H_MATRIX_FILE, h_matrix); 
        end
        
    endgenerate
    
    genvar i;
    generate
        for(i = 0; i < N_ITER; i += 1) begin: gen_interm_layers
            if (i == 0) begin
                interm_layer #(.N_V(N_V), .N_C(N_C), .E(147)) iterm (  .clk(clk),
                                                                       .rst(rst),
                                                                       .tanner_g(tanner_g),
                                                                       .prev_proc_elem(proc_l1),
                                                                       .proc_elem(proc_elem[0]));
            end
            else begin
                interm_layer #(.N_V(N_V), .N_C(N_C), .E(147)) iterm (  .clk(clk),
                                                                       .rst(rst),
                                                                       .tanner_g(tanner_g),
                                                                       .prev_proc_elem(proc_elem[i-1]),
                                                                       .proc_elem(proc_elem[i]));
            end
        end
    endgenerate
    
    in_to_llr #(.N_V(N_V)) inllr (.clk(clk),
                                  .rst(rst),
                                  .cw(cw),
                                  .llr(in_llr));
                                                             
    out_layer #(.N_V(N_V), .N_C(N_C), .E(147)) o_layer (  .clk(clk),
                                                          .rst(rst),
                                                          .tanner_g(tanner_g),
                                                          .prev_proc_elem(proc_elem[N_ITER-1]),
                                                          .out_llr(out_llr));                                                          
    
    // get the edges for the Tanner graph where
    // tanner_g[index][0] - variable node
    // tanner_g[index][1] - check node
    integer t_index = 0;
    always @ (negedge rst) begin
        // init tanner_g    
        for(int i = 0; i < N_C; i += 1) begin
            for(int j = 0; j < N_V; j += 1) begin
                if(h_matrix[i][j] == 1) begin
                    tanner_g[t_index][0] = i;
                    tanner_g[t_index][1] = j;
                    
                    t_index += 1;
                end
            end
        end
    end
    
    // For the first iteration, consider the processing elements = 0
    // so initialize proc_l1 as such
    always @ (negedge rst) begin
        for(int i = 0; i < E; i += 1) begin
            proc_l1[i] = 8'b0;
        end
    end
   
endmodule
