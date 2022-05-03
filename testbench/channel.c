#include "channel.h"
#include "matrix.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

void binary_to_llr(matrix_t* mat, llrParams params){
    
}

int to_defined_int(float* in, int in_size, cint_t* out, int out_size, llrParams params){
    int ret_size = in_size;
    if(out_size < in_size){
        // Only fill until out_size
        ret_size = out_size;
    }

    for (int i = 0; i < ret_size; i++)
    {
        float x = in[i] * (1u << params.dec_point_bit);
        cint_t a = {x};
        if(x > CINT_MAX){
            printf("Warning: Float array conversion to int overflow\n");
            a.x = CINT_MAX;
        }
        if(x < CINT_MIN){
            printf("Warning: Float array conversion to int underflow\n");
            a.x = CINT_MIN;
        }
        out[i] = a;
    }
    return ret_size;
    
}

int from_defined_int(cint_t* in, int in_size, float* out, int out_size, llrParams params){
    int ret_size = in_size;
    if(out_size < in_size){
        // Only fill until out_size
        ret_size = out_size;
    }

    for (int i = 0; i < ret_size; i++)
    {
        out[i] = ((float)in[i].x) / (1u << params.dec_point_bit);
    }
    return ret_size;
    
}