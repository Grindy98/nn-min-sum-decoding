`include "ct.vh"

module interm_layer
    #(  parameter WIDTH = 8,
        parameter N_V = 44,
        parameter E = 147)
    ( input clk, rst,
      input data_ready,
      input prev_ready,
      input [WIDTH * N_V - 1 : 0] all_llrs,
      input [WIDTH * E - 1 : 0] prev_proc_elem,
      output [WIDTH * E - 1 : 0] proc_elem,
      output interm_ready);
    
    wire [WIDTH * E - 1 : 0] proc_elem_v;
    wire [WIDTH * E - 1 : 0] bias;
    wire ready_v;
    
    variable_nodes #(.N_V(N_V), .E(E)) v_layer (.all_llrs(all_llrs),
                                                .prev_proc_elem(prev_proc_elem),
                                                .proc_elem(proc_elem_v));
    
    check_nodes #(.E(E)) c_layer (.bias(bias),
                                  .prev_proc_elem(proc_elem_v),
                                  .proc_elem(proc_elem));
                                  
    always @(posedge clk) begin
        if(rst == `RESET_VAL) begin
            // reset logic here
        end
    end
endmodule
