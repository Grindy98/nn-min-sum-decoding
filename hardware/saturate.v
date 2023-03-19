`include "ct.vh"

module saturate
	#( 
        parameter WIDTH = `LLR_WIDTH,
	    parameter EXTENDED_BITS = `EXTENDED_BITS
    )( 
        input [WIDTH + EXTENDED_BITS - 1 : 0] in,
	    output reg [WIDTH - 1 : 0] out
    );

	localparam MSB = WIDTH + EXTENDED_BITS - 1;
    localparam MAXVAL = ~(1 << (WIDTH - 1));

	always @* begin
        if ( in[MSB -: EXTENDED_BITS + 1] == {(EXTENDED_BITS + 1){1'b0}} ||
             in[MSB -: EXTENDED_BITS + 1] == {(EXTENDED_BITS + 1){1'b1}} ) begin
    
            out = in[MSB - EXTENDED_BITS : 0];
        end
        else if ( in[MSB] == 1'b0 ) begin
            out = MAXVAL; // saturate positive
        end
        else begin
            out = -MAXVAL; // saturate negative
        end
	end

endmodule
