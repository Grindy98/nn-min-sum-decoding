import argparse
import os.path as path

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('i', type=str, nargs=1)
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


def build_source(dict_of_arrays, file_name):
    ret = ''
    ret += f'#include "{file_name}.h"\n'
    for name, val in dict_of_arrays.items():
        is_binary_flag = ((val == 0) | (val == 1)).all()
        ret += get_array(val, name + '_arr')
    # Create init mat function
    ret += 'void init_adj_mats(){\n'
    for name, val in dict_of_arrays.items():
        ret += (f'\t{name}_mat = create_mat({name}_arr, {val.shape[0]}, {val.shape[1]}, '
                f'{1 if is_binary_flag else 0});\n')
    ret += '}\n'
    # Create init mat function
    ret += 'void free_adj_mats(){\n'
    for name in dict_of_arrays.keys():
        ret += f'\tfree_mat(&{name}_mat);\n'
    ret += '}\n'
    return ret

def build_header(dict_of_arrays, file_name):
    ret = ''
    ret += f'#ifndef {file_name.upper()}\n'
    ret += f'#define {file_name.upper()}\n'
    ret += '#include "matrix.h"\n'
    for name in dict_of_arrays.keys():
        ret += f'matrix_t* {name}_mat;\n'
    ret += 'void init_adj_mats();\n'
    ret += 'void free_adj_mats();\n'
    ret += '#endif'
    return ret

def main():
    args = parser.parse_args()
    with open(args.i[0], 'rb') as in_file, open(args.o[0] + '.c', 'w') as out_file_c, open(args.o[0] + '.h', 'w') as out_file_h:
       data = np.load(in_file)
       source_out = build_source(data, args.o[0])
       out_file_c.write(source_out)
       header_out = build_header(data, args.o[0])
       out_file_h.write(header_out)

main()

