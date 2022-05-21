#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#include "matrix.h"
#include "layer.h"
#include "channel.h"
#include "import_matrix_wrapper.h"

int main(){
    // Seed for rng
    srand(time(0));

    init_adj_mats();

    matrix_t* inp_mat;
    matrix_t* prev_mat;
    matrix_t* inp_mat_mask;
    matrix_t* prev_mat_mask;
    matrix_t* bias_mat;
    {
        int64_t inp_arr[] = {1, 2, 3};
        int64_t prev_arr[] = {1, 2, 3, 4, 5};
        int64_t inp_arr_mask[] = {1 , 0, 0, 0, 0,
                                  1 , 1, 0, 0, 0,
                                  0 , 1, 1, 1, 1};

        int64_t prev_arr_mask[] = {1, 0, 0, 0, 0,
                                   1, 1, 0, 0, 0,
                                   0, 1, 1, 0, 1,
                                   0, 1, 0, 0, 1,
                                   0, 1, 0, 1, 0};
        int64_t bias_arr[] = {0, 1, -1, 0, 1};
        inp_mat = create_mat(inp_arr, 1, 3, 0);
        prev_mat = create_mat(prev_arr, 1, 5, 0);
        inp_mat_mask = create_mat(inp_arr_mask, 3, 5, 1);
        prev_mat_mask = create_mat(prev_arr_mask, 5, 5, 1);
        bias_mat = create_mat(bias_arr, 1, 5, 0);
    }
    display_mat(inp_mat_mask);
    matrix_t* extracted_mat = mat_extract(inp_mat_mask, -1, 0);
    printf("\n");
    display_mat(extracted_mat);
    printf("Layer test\n");
    // Odd layer test
    oddlayer_t oddl;
    oddl.input_mask = inp_mat_mask;
    oddl.prev_layer_mask = prev_mat_mask;
    display_mat(inp_mat);
    display_mat(prev_mat);
    matrix_t* out = process_oddlayer(oddl, inp_mat, prev_mat);
    display_mat(out);
    free_mat(&out);

    // Even layer test
    evenlayer_t evenl;
    evenl.prev_layer_mask = prev_mat_mask;
    evenl.biases = bias_mat;
    out = process_evenlayer(evenl, prev_mat);
    display_mat(out);

    printf("Channel tests\n");
    matrix_t* cw = generate_random_codeword(inp_mat_mask);
    display_mat(cw);
    matrix_t* llr_cw = channel_out_llr(cw, 0.2);
    display_mat(llr_cw);

    free_mat(&extracted_mat);
    free_mat(&llr_cw);
    free_mat(&cw);
    free_mat(&out);
    free_mat(&inp_mat);
    free_mat(&prev_mat);
    free_mat(&inp_mat_mask);
    free_mat(&prev_mat_mask);
    free_mat(&bias_mat);
    free_adj_mats();
    return 0;
}