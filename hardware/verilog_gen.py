import numpy as np

import argparse
import sys
import os

import ct


parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, nargs='+')
parser.add_argument('-o', type=str, nargs=1)


def add_parameters(params):
    """Every parameter should be a tuple of the form (name, value)"""
    ret = ''
    first_p = True

    for param in params:
        if first_p:
            ret += f'\t#(  parameter {param[0]} = {param[1]},\n'
            first_p = False
        else:
            ret += f'\t    parameter {param[0]} = {param[1]},\n'

    ret = ret[:-2] + ')\n'
    return ret

def build_varn_source(adj_mat_dict, file_name):
    # extract the number of variable nodes and the number of edges from adj_mat_dict
    n_edges = adj_mat_dict['odd_inp_layer_mask'].shape[1]
    n_v = adj_mat_dict['odd_inp_layer_mask'].shape[0]

    src = ''
    src += '`timescale 1ns / 1ps\n'
    src += f'`define RESET_VAL {ct.RESET_VAL}\n\n'

    # define the module itself
    src += f'module {file_name}\n'

    # add the parameters
    # get no of edge and variables from adj matrices
    src += add_parameters([('WIDTH', ct.WIDTH),
                           ('N_V', n_v),
                           ('E', n_edges)])

    # add the ports
    src += '\t( input clk, rst,\n' +\
            '\t  input data_ready,\n' +\
            '\t  input prev_ready,\n' +\
            '\t  input [WIDTH * N_V - 1 : 0] all_llrs,\n' +\
            '\t  input [WIDTH * E - 1 : 0] prev_proc_elem,\n' +\
            '\t  output [WIDTH * E - 1 : 0] proc_elem,\n' +\
            '\t  output reg varn_ready);\n\n'

    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + 4;\n'

    # add registers

    # temp_reg will be used for the sum with saturation
    src += '\t' + 'reg [EXTENDED_WIDTH * E - 1 : 0] temp_reg, temp_reg_nxt;\n\n'

    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_WIDTH - WIDTH))' +\
            ' sat[E - 1 : 0] (.in(temp_reg), .out(proc_elem));\n\n'

    # sequential logic segment
    src += '\t' + 'always @(posedge clk) begin\n'

    src += '\t\t' + 'if (rst == `RESET_VAL) begin\n'

    src += '\t\t\t' + 'varn_ready <= 1\'b0;\n'

    src += '\t\t' + 'end\n'

    src += '\t\t' +'else if (prev_ready == 1 && data_ready == 1) begin\n'

    src += '\t\t\t' + 'temp_reg <= temp_reg_nxt;\n\n'

    # for every edge (node)
    # for edge_i in range(0, ct.N_EDGES):
        # src += '\t\t\t' + f'proc_elem[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] <= ' +\
        #         f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 2 -: WIDTH];\n'

    src += '\t\t\t' + 'varn_ready <= 1\'b1;\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # combinational logic segment
    src += '\n\t' + 'always @* begin\n'

    src += '\t\t' + 'temp_reg_nxt = temp_reg;\n\n'
    src += '\t\t' + 'if (prev_ready == 1 && data_ready == 1) begin\n'

    # for every edge (node)
    for edge_i in range(0, ct.N_EDGES):
        for prev_i in range(0, ct.N_V):
            if adj_mat_dict['odd_inp_layer_mask'][prev_i][edge_i] == 1:
                src += '\t\t\t' + f'temp_reg_nxt[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                        f'{{{{(EXTENDED_WIDTH - WIDTH){{all_llrs[(WIDTH * {prev_i + 1}) - 1]}}}}, all_llrs[(WIDTH * {prev_i + 1}) - 1 -: WIDTH]}};\n'

        for prev_i in range(0, ct.N_EDGES):
            if adj_mat_dict['odd_prev_layer_mask'][prev_i][edge_i] == 1:
                src += '\t\t\t' + f'temp_reg_nxt[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                        f'temp_reg_nxt[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] + ' +\
                        f'prev_proc_elem[(WIDTH * {prev_i + 1}) - 1 -: WIDTH];\n'
        src += '\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # close the module
    src += 'endmodule\n'

    return src

# atm, just try to generate the even_layer
def main():
    # args.o[0] should be the file name of the generated verilog source
    # args.i should be the files containing the adjacency matrices
    args = parser.parse_args()

    if len(sys.argv) < 3:
        print('Not enough arguments given')
        return

    with open(args.o[0] + '.v', 'w') as out_file:
        data = {}

        for inp in args.i:
            with open(inp, 'rb') as infile:
                if os.path.splitext(inp)[1] == '.npz':
                    data.update(np.load(infile).items())
                else:
                    raise argparse.ArgumentError('Input files do not have proper format')

        source_out = build_varn_source(data, args.o[0])

        # print(data)
        # print('\n')
        # print(source_out)
        out_file.write(source_out)


if __name__ == '__main__':
    main()
