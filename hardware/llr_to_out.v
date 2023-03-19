`include "ct.vh"

module llr_to_out
	#( 
		parameter WIDTH = `LLR_WIDTH
	)(
		input [WIDTH - 1 : 0] in,
	  	output out
	);

	localparam MSB = WIDTH - 1;

    assign out = ~in[MSB];

endmodule