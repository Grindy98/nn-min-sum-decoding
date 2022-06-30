import numpy as np

import argparse
import os

import ct


parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, nargs='+', help='path to needed input file(s)')
parser.add_argument('-var_o', type=str, nargs=1, help='name of the variable nodes module')
parser.add_argument('-check_o', type=str, nargs=1, help='name of the check nodes module')
parser.add_argument('-out_o', type=str, nargs=1, help='name of the output layer module')
parser.add_argument('-lut_o', type=str, nargs=1, help='name of the lut module')

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

        # min + bias
        src += (
            '\t\t' f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = \n'
            '\t\t\t' '{ {EXTENDED_BITS{reg_min[(WIDTH * ' f'{edge_i + 1}' ') - 1]} }, '
            'reg_min[(WIDTH * ' f'{edge_i + 1}' ') - 1 -: WIDTH] } + \n'
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

def build_lut_source(data_dict, file_name):
    # extract the number of variable nodes and the number of edges from adj_mat_dict
    n_edges = data_dict['even_prev_layer_mask'].shape[1]
    src = ''

    src += '// GENERATED FILE -- DO NOT MODIFY DIRECTLY\n'

    src += '`include "ct.vh"\n\n'

    # define the module itself
    src += f'module {file_name}\n'
    # add the ports
    src += (
            '\t( input [`INT_SIZE-1 : 0] bias_idx,\n'
            f'\t  output reg [{ct.WIDTH * n_edges}-1 : 0] bias);\n\n'
    )

    # add always & case block
    src += '\talways@* begin\n'
    src += '\tcase(bias_idx)\n'

    # for every iteration
    for i in range(data_dict['biases'].shape[0]):
        row = data_dict['biases'][i, :]
        bin_str = ''.join([np.binary_repr(x, width=ct.WIDTH) for x in row])
        src += f'\t\t`INT_SIZE\'d{i} : bias = {len(bin_str)}\'b{bin_str};\n'
    
    # add default at the end
    src += '\t\tdefault : bias = 0;\n'

    # close the case & always block
    src += '\tendcase\n'
    src += '\t' + 'end\n'

    # close the module
    src += 'endmodule\n'

    return src

def build_outl_source(adj_mat_dict, file_name):
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
            '\t  output [N_V - 1 : 0] cw_out);\n\n'

    src += '\t' + 'localparam EXTENDED_WIDTH = WIDTH + EXTENDED_BITS;\n\n'

    # add registers
    # temp_reg will be used for the sum with saturation
    src += '\t' + 'reg [EXTENDED_WIDTH * N_V - 1 : 0] temp_reg;\n\n'
    src += '\t' + 'wire [WIDTH * N_V - 1 : 0] llr_out_wire;\n\n'

    # instantiate the saturation module
    src += '\t' + 'saturate #(.WIDTH(WIDTH), .EXTENDED_BITS(EXTENDED_BITS))' +\
            ' sat[N_V - 1 : 0] (.in(temp_reg), .out(llr_out_wire));\n'

    # instantiate the hard decision extraction module
    src += '\t' + 'llr_to_out #(.WIDTH(WIDTH)) ' +\
                'lto[N_V - 1 : 0] (.in(llr_out_wire), .out(cw_out));\n\n'            

    # combinational logic segment
    src += '\n\t' + 'always @* begin\n'
    def generate_inp(edge_i, n_tabs):
        return (
            n_tabs*'\t' + '{ {EXTENDED_BITS{all_llrs[WIDTH * ' f'{edge_i + 1}' ' - 1]} }, '
            'all_llrs[(WIDTH * ' f'{edge_i + 1}' ') - 1 -: WIDTH] }'
        )
    
    def generate_prev(prev_i, n_tabs):
        return (
            n_tabs*'\t' + '{ {EXTENDED_BITS{prev_proc_elem[(WIDTH * ' f'{prev_i + 1}' ') - 1]} }, '
            'prev_proc_elem[(WIDTH * ' f'{prev_i + 1}' ') - 1 -: WIDTH] }'
        )

    # for every edge (node)
    for edge_i in range(0, n_v):
        src += '\t\t' + f'temp_reg[(EXTENDED_WIDTH * {edge_i + 1}) - 1 -: EXTENDED_WIDTH] = \n'
        inp_str_lst = []
        inp_str_lst.append(generate_inp(edge_i, 3))

        prev_str_lst = []
        for prev_i in range(0, n_edges):
            if adj_mat_dict['output_mask'][prev_i][edge_i] == 1:
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


def generate_module(file_name, data, gen_func):
    with open(file_name + '.v', 'w') as out_file:
        source_out = gen_func(data, file_name)
        out_file.write(source_out)
        print(f"Written {file_name + '.v'}")


def main():
    args = parser.parse_args()
    data = {}

    for inp in args.i:
        with open(inp, 'rb') as infile:
            if os.path.splitext(inp)[1] == '.npz':
                data.update(np.load(infile).items())
            elif os.path.splitext(inp)[1] == '.npy':
                data[os.path.basename(os.path.splitext(inp)[0])] = np.load(infile)
            else:
                raise argparse.ArgumentError('Input files do not have proper format')

    # generate the variable nodes module
    generate_module(args.var_o[0], data, build_varn_source)

    # generate the check nodes module
    generate_module(args.check_o[0], data, build_checkn_source)
    
    # generate the output layer module
    generate_module(args.out_o[0], data, build_outl_source)

    # generate the lut module
    generate_module(args.lut_o[0], data, build_lut_source)


if __name__ == '__main__':
    main()
