`include "ct.vh"

module interm_layer
    #(  parameter WIDTH = 8,
        parameter N_V = 44,
        parameter E = 147)
    ( input [`INT_SIZE-1 : 0] bias_idx,
      input [WIDTH * N_V - 1 : 0] all_llrs,
      input [WIDTH * E - 1 : 0] prev_proc_elem,
      output [WIDTH * E - 1 : 0] proc_elem);
    
    wire [WIDTH * E - 1 : 0] proc_elem_v;
    wire [WIDTH * E - 1 : 0] bias;
    
    variable_nodes #(.WIDTH(WIDTH), .N_V(N_V), .E(E)) v_layer (.all_llrs(all_llrs),
                                                .prev_proc_elem(prev_proc_elem),
                                                .proc_elem(proc_elem_v));
    
    check_nodes #(.WIDTH(WIDTH), .E(E)) c_layer (.bias(0),
                                  .prev_proc_elem(proc_elem_v),
                                  .proc_elem(proc_elem));
                                  
endmodule
