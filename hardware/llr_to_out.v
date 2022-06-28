`include "ct.vh"

module llr_to_out
	#( parameter WIDTH = 8)
	( input [WIDTH - 1 : 0] in,
	  output reg out);

	localparam MSB = WIDTH - 1;

    assign out = in[MSB];

endmodule