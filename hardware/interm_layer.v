`include "ct.vh"

module interm_layer
    #(  
        parameter WIDTH,
        parameter N_V,
        parameter E,
        parameter EXTENDED_BITS
    )( 
        input [`INT_SIZE-1 : 0] bias_idx,
        input [WIDTH * N_V - 1 : 0] all_llrs,
        input [WIDTH * E - 1 : 0] prev_proc_elem,
        output [WIDTH * E - 1 : 0] proc_elem
    );
    
    wire [WIDTH * E - 1 : 0] proc_elem_v;
    wire [WIDTH * E - 1 : 0] bias;
    
    lut_biases lut(
        .bias_idx(bias_idx),
        .bias(bias)
    );
    
    variable_nodes #(.WIDTH(WIDTH), .N_V(N_V), .E(E), .EXTENDED_BITS(EXTENDED_BITS)) v_layer (
        .all_llrs(all_llrs),
        .prev_proc_elem(prev_proc_elem),
        .proc_elem(proc_elem_v)
    );
    
    check_nodes #(.WIDTH(WIDTH), .E(E), .EXTENDED_BITS(EXTENDED_BITS)) c_layer (
        .bias(bias),
        .prev_proc_elem(proc_elem_v),
        .proc_elem(proc_elem)
    );                          
endmodule
