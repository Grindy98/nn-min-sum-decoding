
import argparse


import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('i', type=str, nargs=1)
parser.add_argument('o', type=str, nargs=1)

def get_array(arr, arr_name):
    if len(arr.shape) != 2:
        raise ValueError("Numpy array has to be a matrix")
    ret = ''
    ret += f'cint_t {arr_name}[] = {{\n'
    row_list = []
    for i in range(arr.shape[0]):
        row = '\t'
        row += ', '.join([f'{{{x}}}' for x in arr[i, :]])
        row_list.append(row)
    ret += ',\n'.join(row_list)
    ret += '\n};\n'
    return ret


def build_header(dict_of_arrays):
    ret = ''
    ret += '#include "matrix.h"\n'
    for name in dict_of_arrays.keys():
        ret += f'matrix* {name}_mat;\n'
    ret += '{\n'
    for name, val in dict_of_arrays.items():
        ret += get_array(val, name + '_arr')
        ret += f'{name}_mat = create_matrix({name}_arr, {val.shape[0]}, {val.shape[1]});\n'
    ret += '}\n'
    return ret

def main():
    #args = parser.parse_args()
    #with open(args.i[0], 'r') as in_file, open(args.o[0], 'w') as out_file:
    #    pass
    np_arr = np.arange(12).reshape(3, 4)
    print(build_header({'first': np_arr}))   

main()

