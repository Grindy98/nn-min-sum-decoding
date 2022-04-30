#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "matrix.h"
#include "layer.h"

int main(){
    matrix* inp_mat;
    matrix* prev_mat;
    matrix* inp_mat_mask;
    matrix* prev_mat_mask;
    matrix* bias_mat;
    {
        int inp_arr[] = {1, 2, 3};
        int prev_arr[] = {1, 2, 3, 4, 5};
        int inp_arr_mask[] = {1, 0, 0, 0, 0,
                            1, 1, 0, 0, 0,
                            0, 1, 1, 1, 1};

        int prev_arr_mask[] = {1, 0, 0, 0, 0,
                            1, 1, 0, 0, 0,
                            0, 1, 1, 0, 1,
                            0, 1, 0, 0, 1,
                            0, 1, 0, 1, 0};
        int bias_arr[] = {0, 1, -1, 0, 1};
        inp_mat = create_mat(inp_arr, 1, 3);
        prev_mat = create_mat(prev_arr, 1, 5);
        inp_mat_mask = create_mat(inp_arr_mask, 3, 5);
        prev_mat_mask = create_mat(prev_arr_mask, 5, 5);
        bias_mat = create_mat(bias_arr, 1, 5);
    }
    // Odd layer test
    oddlayer oddl;
    oddl.input_mask = inp_mat_mask;
    oddl.prev_layer_mask = prev_mat_mask;
    display_mat(inp_mat);
    display_mat(prev_mat);
    matrix* out = process_oddlayer(oddl, inp_mat, prev_mat);
    display_mat(out);
    free_mat(&out);

    // Even layer test
    evenlayer evenl;
    evenl.prev_layer_mask = prev_mat_mask;
    evenl.biases = bias_mat;
    out = process_evenlayer(evenl, prev_mat);
    display_mat(out);
    free_mat(&out);
    free_mat(&inp_mat);
    free_mat(&prev_mat);
    free_mat(&inp_mat_mask);
    free_mat(&prev_mat_mask);
    free_mat(&bias_mat);
    return 0;
}