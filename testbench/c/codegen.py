import argparse
import os.path as path
import json

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('i', type=str, nargs='+')
parser.add_argument('-p', type=str, nargs=1)
parser.add_argument('-o', type=str, nargs=1)

def get_array(arr, arr_name):
    if len(arr.shape) != 2:
        raise ValueError("Numpy array has to be a matrix")
    ret = ''
    ret += f'int64_t {arr_name}[] = {{\n'
    row_list = []
    for i in range(arr.shape[0]):
        row = '\t'
        row += ', '.join([f'{x}' for x in arr[i, :]])
        row_list.append(row)
    ret += ',\n'.join(row_list)
    ret += '\n};\n'
    return ret


def build_source(dict_of_arrays, params, file_name):
    ret = ''
    ret += '// GENERATED FILE -- DO NOT MODIFY DIRECTLY\n'
    ret += f'#include "{file_name}.h"\n'
    # Define const params
    ret += f'const char MODEL_KEY[] = "{params["MODEL_KEY"]}";\n'
    ret += f'const int DEFAULT_LLR = {params["DEFAULT_LLR"]};\n'
    ret += f'const int CINT_SIZE = {params["LLR_WIDTH"]};\n'
    ret += f'const double CROSS_P = {params["CROSS_P"]};\n'
    # Define arrays
    for name, val in dict_of_arrays.items():
        ret += get_array(val, name + '_arr')
    # Define matrices
    for name, val in dict_of_arrays.items():
        ret += f'matrix_t* {name}_mat;\n'
    # Create init mat function
    ret += 'void init_adj_mats(){\n'
    for name, val in dict_of_arrays.items():
        is_binary_flag = ((val == 0) | (val == 1)).all()
        ret += (f'\t{name}_mat = create_mat({name}_arr, {val.shape[0]}, {val.shape[1]}, '
                f'{1 if is_binary_flag else 0});\n')
    ret += '}\n'
    # Create init mat function
    ret += 'void free_adj_mats(){\n'
    for name in dict_of_arrays.keys():
        ret += f'\tfree_mat(&{name}_mat);\n'
    ret += '}\n'
    return ret

def main():
    args = parser.parse_args()
    with open(args.o[0] + '.c', 'w') as out_file_c:
        data = {}
        params = {}
        for inp in args.i:
            with open(inp, 'rb') as infile:
                if path.splitext(inp)[1] == '.npz':
                    data.update(np.load(infile).items())
                elif path.splitext(inp)[1] == '.npy':
                    data[path.basename(path.splitext(inp)[0])] = np.load(infile)
                else:
                    raise argparse.ArgumentError('Input files do not have proper format')

        with open(args.p[0], 'r') as infile:
            params = json.load(infile)

        source_out = build_source(data, params, args.o[0])
        out_file_c.write(source_out)

main()

