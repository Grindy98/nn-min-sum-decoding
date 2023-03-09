interface axi_stream_if 
	#(
        parameter WIDTH = 32
	)();
	logic tvalid;
	logic tready;
	logic tlast;
	logic [WIDTH-1:0] tdata;

	modport slave (
		input tvalid, tlast, tdata, output tready
	);

	modport master (
		output tvalid, tlast, tdata, input tready
	);

endinterface