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

    src += '// GENERATED FILE -- DO NOT MODIFY DIRECTLY\n'

    src += '`include "ct.vh"\n\n'

    # define the module itself
    src += f'module {file_name}\n'

    # add the parameters
    src += add_parameters([('WIDTH', ct.WIDTH),
                           ('N_V', n_v),
                           ('E', n_edges),
                           ('EXTENDED_BITS', 4)])

    # add the ports
    src +=  '\t( input [WIDTH * N_V - 1 : 0] all_llrs,\n' +\
            '\t  input [WIDTH * E - 1 : 0] prev_proc_elem,\n' +\
            '\t  output [WIDTH * E - 1 : 0] proc_elem);\n\n'

    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + EXTENDED_BITS;\n\n'

    # add registers
    # temp_reg will be used for the sum with saturation
    src += '\t' + 'reg [EXTENDED_WIDTH * E - 1 : 0] temp_reg;\n\n'

    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_BITS))' +\
            ' sat[E - 1 : 0] (.in(temp_reg), .out(proc_elem));\n\n'

    # combinational logic segment

    src += '\n\t' + 'always @* begin\n'
    def generate_inp(prev_i, n_tabs):
        return (
            n_tabs*'\t' + '{ {EXTENDED_BITS{all_llrs[WIDTH * ' f'{prev_i + 1}' ' - 1]} }, '
            'all_llrs[(WIDTH * ' f'{prev_i + 1}' ') - 1 -: WIDTH] }'
        )
    
    def generate_prev(prev_i, n_tabs):
        return (
            n_tabs*'\t' + '{ {EXTENDED_BITS{prev_proc_elem[(WIDTH * ' f'{prev_i + 1}' ') - 1]} }, '
            'prev_proc_elem[(WIDTH * ' f'{prev_i + 1}' ') - 1 -: WIDTH] }'
        )

    # for every edge (node)
    for edge_i in range(0, n_edges):
        src += '\t\t' + f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = \n'
        inp_str_lst = []
        for prev_i in range(0, n_v):
            if adj_mat_dict['odd_inp_layer_mask'][prev_i][edge_i] == 1:
                inp_str_lst.append(generate_inp(prev_i, 3))

        prev_str_lst = []
        for prev_i in range(0, n_edges):
            if adj_mat_dict['odd_prev_layer_mask'][prev_i][edge_i] == 1:
                prev_str_lst.append(generate_prev(prev_i, 3))
        
        src += ' +\n\n'.join(filter(None, [
            ' +\n'.join(inp_str_lst),
            ' +\n'.join(prev_str_lst)
        ]))
        src += ';\n\n'

    # close the always block
    src += '\t' + 'end\n'

    # close the module
    src += 'endmodule\n'

    return src


def build_checkn_source(adj_mat_dict, file_name):
    # extract the number of variable nodes and the number of edges from adj_mat_dict
    n_edges = adj_mat_dict['even_prev_layer_mask'].shape[1]
    src = ''

    src += '// GENERATED FILE -- DO NOT MODIFY DIRECTLY\n'

    src += '`include "ct.vh"\n\n'

    # define the module itself
    src += f'module {file_name}\n'

    # add the parameters
    src += add_parameters([('WIDTH', ct.WIDTH),
                           ('E', n_edges),
                           ('EXTENDED_BITS', 4)])

    # add the ports
    src += (
            '\t( input [WIDTH * E - 1 : 0] bias,\n'
            '\t  input [WIDTH * E - 1 : 0] prev_proc_elem,\n'
            '\t  output [WIDTH * E - 1 : 0] proc_elem);\n\n'
    )
    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + EXTENDED_BITS;\n\n'

    # add registers
    src += '\t' + 'reg [WIDTH * E - 1 : 0] abs_prev_proc_elem;\n'
    src += '\t' + 'reg [E - 1 : 0] reg_sign;\n'
    src += '\t' + 'reg [WIDTH * E - 1 : 0] reg_min;\n'
    src += '\t' + 'reg [EXTENDED_WIDTH * E - 1 : 0] temp_reg;\n\n'
    src += '\t' + 'integer i;\n\n'
    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_BITS))' +\
            ' sat[E - 1 : 0] (.in(temp_reg), .out(proc_elem));\n\n'

    # combinational logic segment
    src += '\n\t' + 'always @* begin\n'

    src += (
        '\t\tfor(i = 1; i <= E; i = i + 1) begin \n'
        '\t\t\tabs_prev_proc_elem[(WIDTH * i) - 1 -: WIDTH] = prev_proc_elem[(WIDTH * i) - 1] == 1\'b1 ?\n'
        '\t\t\t-prev_proc_elem[(WIDTH * i) - 1 -: WIDTH] : prev_proc_elem[(WIDTH * i) - 1 -: WIDTH];\n'
        '\t\tend\n\n'

    )

    src += "\t\treg_min = {E{ {1'b0, {WIDTH-1{1'b1}} } }};\n"
    src += "\t\treg_sign = {E{1'b0}};\n\n"

    # for every edge (node)
    for edge_i in range(0, n_edges):
        src += '\t\t' + f'//----- edge #{edge_i}\n'

        for prev_i in range(0, n_edges):
            if adj_mat_dict['even_prev_layer_mask'][prev_i][edge_i] == 1:
                # get the minimum
                src += '\t\t' + f'if (reg_min[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] > abs_prev_proc_elem[(WIDTH * {edge_i + 1}) - 1 -: WIDTH]) begin\n'
                src += '\t\t\t' + f'reg_min[(WIDTH * {edge_i + 1}) - 1 -: WIDTH] = abs_prev_proc_elem[(WIDTH * {edge_i + 1}) - 1 -: WIDTH];\n'
                src += '\t\t' + 'end\n'

                src += '\n\t\t' + f'reg_sign[{edge_i}] = reg_sign[{edge_i}] ^ prev_proc_elem[(WIDTH * {prev_i + 1}) - 1];\n\n'

        # min - bias
        src += (
            '\t\t' f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = \n'
            '\t\t\t' '{ {EXTENDED_BITS{reg_min[(WIDTH * ' f'{edge_i + 1}' ') - 1]} }, '
            'reg_min[(WIDTH * ' f'{edge_i + 1}' ') - 1 -: WIDTH] } - \n'
            '\t\t\t' '{ {EXTENDED_BITS{bias[(WIDTH * ' f'{edge_i + 1}' ') - 1]} }, '
            'bias[(WIDTH * ' f'{edge_i + 1}' ') - 1 -: WIDTH] };\n\n'
        )
        # max(min-bias, 0) - clip to zero if negative
        src +=  (
            f'\t\ttemp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1] == 1\'b1 ? \n'
            f'\t\t{{EXTENDED_WIDTH{{1\'b0}}}} : temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH];\n\n'
        )

        # sign * magnitude
        src +=  (
            f'\t\ttemp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = reg_sign[{edge_i}] == 1\'b1 ? \n'
            f'\t\t-temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] : temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH];\n'
        )
        src += '\n'
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
