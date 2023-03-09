`include "ct.vh"
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11.06.2022 16:08:19
// Design Name: 
// Module Name: tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


class cw_wrapper #(
    parameter N_V,
    parameter LLR_WIDTH);
    logic[N_V-1:0][LLR_WIDTH-1:0] cw ;
endclass

module tb();

import "DPI-C" function void before_start(); 
import "DPI-C" function void before_end(); 

import "DPI-C" function void pass_through_model(input int cw[], output logic cw_out[]);

import "DPI-C" function int generate_cw_init(output logic cw[]);
import "DPI-C" function int generate_cw_noisy_from_init(output logic cw_out[], input logic cw_in[], input real cross_p, input int n_errors);
import "DPI-C" function int cast_cw_to_llr(output int cw_out[], input logic cw_in[]);
import "DPI-C" function int generate_noisy_llr_cw(output int cw[], input real cross_p, input int n_errors);

/*
export "DPI-C" function c_print_wrapper;

function void c_print_wrapper(input string to_print);
    $write("%s", to_print);
endfunction
*/

localparam LLR_WIDTH = `LLR_WIDTH;
localparam AXI_WIDTH = `AXI_WIDTH;
localparam N_V = `N_V;
localparam E = `E;
localparam cross_p = `CROSS_P;

reg clk;
reg rst;

// Create connections

axi_stream_if #(
    .WIDTH(AXI_WIDTH)
) tb_to_dut(), dut_to_tb();

decoder_top dut (
    .clk(clk),
    .rst(rst),
    .from_env(tb_to_dut.slave),
    .to_env(dut_to_tb.master)
);

initial begin
    clk = 0;
    forever #50 clk = ~clk;
end

initial begin
    rst = 1;
    // Initialize input data of interfaces
    tb_to_dut.tvalid = 1'b0;
    tb_to_dut.tlast = 1'b0;
    tb_to_dut.tdata = 'z;

    dut_to_tb.tready = 1'b0;
    #200 rst = 0;
end



mailbox gen_to_dut = new(1);
mailbox dut_to_chk = new(1);
mailbox gen_to_chk_init = new(1);
mailbox gen_to_chk_c = new(1);

task static generate_cw;
    int flag;
    int i; 
    automatic cw_wrapper #(
        .N_V(N_V),
        .LLR_WIDTH(LLR_WIDTH)
    ) w;
    logic generated_cw_initial[N_V-1:0];
    logic [N_V-1:0] cw_initial_packed;
    logic generated_cw_noisy[N_V-1:0];
    logic [N_V-1:0] cw_noisy_packed;
    int llr_cw_noisy[N_V-1:0];

    logic passed_cw [N_V-1:0];
    logic [N_V-1:0] passed_cw_packed;
    logic [LLR_WIDTH-1:0] cw_bit [N_V];

    generated_cw_initial = '{N_V{0}};
    forever begin
        #500 $display("Generating signal - %d", $time());
        
        flag = generate_cw_init(generated_cw_initial);
        if(flag == 1) begin
            $display("Metaparameters don't match");
            $finish;
        end
        
        flag = generate_cw_noisy_from_init(generated_cw_noisy, generated_cw_initial, cross_p, 1);
        if(flag == 1) begin
            $display("Metaparameters don't match");
            $finish;
        end

        flag = cast_cw_to_llr(llr_cw_noisy, generated_cw_noisy);
        if(flag == 1) begin
            $display("Metaparameters don't match");
            $finish;
        end
        
        w = new();
        for (i=0; i<N_V; i=i+1) begin
            w.cw[i] = llr_cw_noisy[i];
        end
        // Send to dut
        gen_to_dut.put(w);
        
        // Get output from init and C model and send for checking
        cw_initial_packed = {<<1{generated_cw_initial}};
        gen_to_chk_init.put(cw_initial_packed);
        cw_noisy_packed = {<<1{generated_cw_noisy}};
        gen_to_chk_init.put(cw_noisy_packed);

        pass_through_model(llr_cw_noisy, passed_cw);
        passed_cw_packed = {<<1{passed_cw}};
        gen_to_chk_c.put(passed_cw_packed);
        
    end 
endtask 

logic[N_V-1:0][LLR_WIDTH-1:0] debug_driver_input;

task static drive_dut;
    automatic cw_wrapper #(
        .N_V(N_V),
        .LLR_WIDTH(LLR_WIDTH)
    ) w;
    static bit data_available = 0;
    static int buf_size = 0;
    static int llr_index = 0;
    static logic [(AXI_WIDTH + LLR_WIDTH)-1 : 0] buffer;
    forever begin
            
        @(posedge clk);
        tb_to_dut.tvalid <= 1'b0;
        tb_to_dut.tlast <= 1'b0;
        tb_to_dut.tdata <= 'z;
        
        // Check if during the last cycle data was sent
        if(tb_to_dut.tvalid && tb_to_dut.tready) begin
            buf_size -= tb_to_dut.WIDTH;
        end

        // Check if we have reached the end
        if(llr_index == N_V && buf_size < tb_to_dut.WIDTH) begin
            assert(buf_size == 0);
            data_available = 0;
        end

        if(!data_available) begin
            if(gen_to_dut.try_peek(w) == 0) begin
                // We do not have data => skip cycle
                continue;
            end
            // Get the data 
            gen_to_dut.get(w);
            data_available = 1;
            buf_size = tb_to_dut.WIDTH - ((LLR_WIDTH*N_V -1) % tb_to_dut.WIDTH + 1); // Start the buffer with the padding size
            buffer = 0;
            llr_index = 0;
        end    

        // Collect data from w into buffer
        while (buf_size < tb_to_dut.WIDTH) begin
            assert(llr_index < N_V);
            buffer = {buffer, w.cw[llr_index]};
            llr_index += 1;
            buf_size += LLR_WIDTH;
        end

        // Drive the bus and other signals
        tb_to_dut.tvalid <= 1'b1;
        tb_to_dut.tdata <= buffer[buf_size-1 -: tb_to_dut.WIDTH];
        tb_to_dut.tlast <= (llr_index == N_V && buf_size == tb_to_dut.WIDTH) ? 1'b1 : 1'b0;
    end
endtask

task static monitor_dut;
    static logic [N_V-1 : 0] read_bits = 0;
    static int cnt = 0;
    forever begin
        @(posedge clk);
        dut_to_tb.tready <= 1'b1;
        // Check if databus valid
        if(dut_to_tb.tvalid) begin
            // Read the input
            read_bits = {read_bits, dut_to_tb.tdata};
            if(dut_to_tb.tlast) begin
                // Finished
                dut_to_chk.put(read_bits);
                read_bits = 0;
            end
        end
        
        cnt <= cnt+1;
        if(cnt % 10 != 0) begin
            dut_to_tb.tready <= 1'b0;
        end
        
    end 
endtask

task static check_cw; 
    automatic logic [N_V-1:0] cw_init;
    automatic logic [N_V-1:0] cw_noisy;
    automatic logic [N_V-1:0] cw_out_c;
    automatic logic [N_V-1:0] cw_out_dut;
    forever begin
        gen_to_chk_init.get(cw_init);
        gen_to_chk_init.get(cw_noisy);
        gen_to_chk_c.get(cw_out_c);
        dut_to_chk.get(cw_out_dut);

        $display("Receiving resulting signals");
        $displayb(cw_init);
        $displayb(cw_noisy);
        $displayb(cw_out_c);
        $displayb(cw_out_dut);
        if(cw_init != cw_out_c) begin
            if(cw_noisy == cw_out_c)begin
                $display("---- MISTAKE UNCORRECTED -----");
            end else begin
                $display("----- WRONG CORRECTION ------");
            end
        end
        if(cw_out_c != cw_out_dut) begin
            $display("--------- MISMATCH ----------");
        end
    end 
endtask 

initial begin
    before_start();
    fork
        generate_cw();
        drive_dut();
        monitor_dut();
        check_cw();
    join
    before_end();
end

endmodule
