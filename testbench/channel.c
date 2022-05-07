#include "channel.h"
#include <stdio.h>
#include <stdlib.h>

matrix_t* generate_random_codeword(matrix_t* gen_mat){
    if(!gen_mat->is_mod_two){
        printf("Generator matrix has to be mod 2\n");
        exit(1);
    }
    // Generate exactly as many bits as expected by the input
    cint_t random_arr[gen_mat->row_size];
    for (int i = 0; i < gen_mat->row_size; i++)
    {
        random_arr[i] = (cint_t){rand() % 2};
    }
    matrix_t* new_inp = create_mat(random_arr, 1, gen_mat->row_size, 1);
    matrix_t* ret = mat_mul(new_inp, gen_mat);
    free_mat(&new_inp);
    return ret;
}

// matrix_t* generate(matrix_t* inp, matrix_t* gen_mat){
//     if(inp->row_size != 1){
//         printf("Input has to be row vector\n");
//         exit(1);
//     }
//     return mat_mul(inp, gen_mat);
// }