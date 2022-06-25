import numpy as np

import argparse
import os

import ct


parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, nargs='+', help='path to needed input file(s)')
parser.add_argument('-var_o', type=str, nargs=1, help='name of the variable nodes module')
parser.add_argument('-check_o', type=str, nargs=1, help='name of the check nodes module')


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

    src += '`include "ct.vh"\n\n'

    # define the module itself
    src += f'module {file_name}\n'

    # add the parameters
    src += add_parameters([('WIDTH', ct.WIDTH),
                           ('N_V', n_v),
                           ('E', n_edges),
                           ('EXTENDED_BITS', 4)])

    # add the ports
    src += '\t( input clk, rst,\n' +\
            '\t  input data_ready,\n' +\
            '\t  input prev_ready,\n' +\
            '\t  input [WIDTH * N_V - 1 : 0] all_llrs,\n' +\
            '\t  input [WIDTH * E - 1 : 0] prev_proc_elem,\n' +\
            '\t  output [WIDTH * E - 1 : 0] proc_elem,\n' +\
            '\t  output reg varn_ready);\n\n'

    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + EXTENDED_BITS;\n\n'

    # add registers
    # temp_reg will be used for the sum with saturation
    src += '\t' + 'reg [EXTENDED_WIDTH * E - 1 : 0] temp_reg, temp_reg_nxt;\n\n'

    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_BITS))' +\
            ' sat[E - 1 : 0] (.in(temp_reg), .out(proc_elem));\n\n'

    # sequential logic segment
    src += '\t' + 'always @(posedge clk) begin\n'

    src += '\t\t' + 'if (rst == `RESET_VAL) begin\n'

    src += '\t\t\t' + 'varn_ready <= 1\'b0;\n'

    src += '\t\t' + 'end\n'

    src += '\t\t' +'else if (prev_ready == 1 && data_ready == 1) begin\n'

    src += '\t\t\t' + 'temp_reg <= temp_reg_nxt;\n\n'
    src += '\t\t\t' + 'varn_ready <= 1\'b1;\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # combinational logic segment
    src += '\n\t' + 'always @* begin\n'

    src += '\t\t' + 'temp_reg_nxt = temp_reg;\n\n'
    src += '\t\t' + 'if (prev_ready == 1 && data_ready == 1) begin\n'

    # for every edge (node)
    for edge_i in range(0, n_edges):
        for prev_i in range(0, n_v):
            if adj_mat_dict['odd_inp_layer_mask'][prev_i][edge_i] == 1:
                src += '\t\t\t' + f'temp_reg_nxt[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                        f'{{{{EXTENDED_BITS{{all_llrs[(WIDTH * {prev_i + 1}) - 1]}}}}, ' +\
                        f'all_llrs[(WIDTH * {prev_i + 1}) - 1 -: WIDTH]}} \n'

        for prev_i in range(0, n_edges):
            if adj_mat_dict['odd_prev_layer_mask'][prev_i][edge_i] == 1:
                src += '\t\t\t\t' + f'+ {{{{EXTENDED_BITS{{prev_proc_elem[(WIDTH * {prev_i + 1}) - 1]}}}}, ' +\
                        f'prev_proc_elem[(WIDTH * {prev_i + 1}) - 1 -: WIDTH]}}\n'
        
        src = src[:-1] +';\n\n'

        src += '\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # close the module
    src += 'endmodule\n'

    return src


def build_checkn_source(adj_mat_dict, file_name):
    # extract the number of variable nodes and the number of edges from adj_mat_dict
    n_edges = adj_mat_dict['even_prev_layer_mask'].shape[1]
    src = ''

    src += '`include "ct.vh"\n\n'

    # define the module itself
    src += f'module {file_name}\n'

    # add the parameters
    src += add_parameters([('WIDTH', ct.WIDTH),
                           ('E', n_edges),
                           ('EXTENDED_BITS', 4)])

    # add the ports
    src += '\t( input clk, rst,\n' +\
            '\t  input prev_ready,\n' +\
            '\t  input bias_ready,\n' +\
            '\t  input [WIDTH * E - 1 : 0] bias,\n' +\
            '\t  input [WIDTH * E - 1 : 0] prev_proc_elem,\n' +\
            '\t  output [WIDTH * E - 1 : 0] proc_elem,\n' +\
            '\t  output reg checkn_ready);\n\n'

    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + EXTENDED_BITS;\n\n'

    # add registers
    src += '\t' + 'reg [WIDTH - 1 : 0] abs_val;\n'
    src += '\t' + 'reg [E - 1 : 0] reg_sign, reg_sign_nxt;\n'
    src += '\t' + 'reg [WIDTH * E - 1 : 0] reg_min, reg_min_nxt;\n'
    src += '\t' + 'reg [EXTENDED_WIDTH * E - 1 : 0] temp_reg;\n\n'

    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_BITS))' +\
            ' sat[E - 1 : 0] (.in(temp_reg), .out(proc_elem));\n\n'

    # sequential logic segment
    src += '\t' + 'always @(posedge clk) begin\n'

    src += '\t\t' + 'if (rst == `RESET_VAL) begin\n'

    src += '\t\t\t' + 'checkn_ready <= 1\'b0;\n'

    # set the minimums register as being the max positive number
    src += '\t\t\t' + f'reg_min <= ~{{E{{1\'b1 << (EXTENDED_WIDTH - 1)}}}};\n'

    src += '\t\t' + 'end\n'

    src += '\t\t' +'else if (prev_ready == 1 && bias_ready == 1) begin\n'

    src += '\t\t\t' + 'reg_sign <= reg_sign_nxt;\n'
    src += '\t\t\t' + 'reg_min <= reg_min_nxt;\n\n'
    src += '\t\t\t' + 'checkn_ready <= 1\'b1;\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # combinational logic segment
    src += '\n\t' + 'always @* begin\n'

    src += '\t\t' + 'reg_sign_nxt = reg_sign;\n'
    src += '\t\t' + 'reg_min_nxt = reg_min;\n\n'

    src += '\t\t' + 'if (prev_ready == 1 && bias_ready == 1) begin\n'

    # for every edge (node)
    for edge_i in range(0, n_edges):
        src += '\t\t\t' + f'//----- edge #{edge_i}\n'

        for prev_i in range(0, n_edges):
            if adj_mat_dict['even_prev_layer_mask'][prev_i][edge_i] == 1:
                # get the absolute value of the prev proc elem
                # TODO probably a register with all of the absolute values will be needed
                src += '\t\t\t' + f'abs_val = (prev_proc_elem[(WIDTH * {prev_i + 1}) - 1] == 1\'b1) ? -prev_proc_elem : prev_proc_elem;\n'

                # get the minimum
                src += '\t\t\t' + f'if (reg_min_nxt[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] > abs_val) begin\n'
                src += '\t\t\t\t' + f'reg_min_nxt[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] = abs_val;\n'
                src += '\t\t\t' + 'end\n'

                src += '\n\t\t\t' + f'reg_sign_nxt[{edge_i}] = reg_sign_nxt[{edge_i}] ^ prev_proc_elem[(WIDTH * {prev_i + 1}) - 1];\n\n'

        # min - bias
        # should probably extend the sign of this operation
        src += '\t\t\t' + f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                            f'reg_min_nxt[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] - ' +\
                            f'bias[(WIDTH * {edge_i + 1}) - 1 -: WIDTH];\n'
        
        # max(min-bias, 0) - clip to zero if negative
        src += '\t\t\t' + f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                            f'(temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1] == 1\'b1)? ' +\
                            f'{{EXTENDED_WIDTH{{1\'b0}}}} : temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH];\n'

        # sign * magnitude
        src += '\t\t\t' + f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = ' +\
                            f'temp_reg[temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH]] * ' +\
                            f'reg_sign_nxt[{edge_i}];\n'

        src += '\n'

    src += '\t\t' + 'end\n'

    # close the always block
    src += '\t' + 'end\n'

    # close the module
    src += 'endmodule\n'

    return src


def main():
    args = parser.parse_args()
    data = {}

    for inp in args.i:
        with open(inp, 'rb') as infile:
            if os.path.splitext(inp)[1] == '.npz':
                data.update(np.load(infile).items())
            else:
                raise argparse.ArgumentError('Input files do not have proper format')

    # generate the variable nodes module
    with open(args.var_o[0] + '.v', 'w') as out_file_v:
        source_out = build_varn_source(data, args.var_o[0])
        out_file_v.write(source_out)
        print(f"Written {args.var_o[0] + '.v'}")

    # generate the check nodes module
    with open(args.check_o[0] + '.v', 'w') as out_file_c:
        source_out = build_checkn_source(data, args.check_o[0])
        out_file_c.write(source_out)
        print(f"Written {args.check_o[0] + '.v'}")



if __name__ == '__main__':
    main()
