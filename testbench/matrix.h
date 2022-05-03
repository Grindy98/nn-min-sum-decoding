#ifndef MATRIX
#define MATRIX

#include "custom_int.h"

typedef struct matrix_t{
    int row_size;
    int col_size;
    cint_t* mat;
} matrix_t;

matrix_t* create_mat(cint_t* arr, int rows, int cols);

matrix_t* duplicate_mat(matrix_t* mat);

int check_range(matrix_t* mat, int row, int col);

cint_t get_elem(matrix_t* mat, int row, int col);

void put_elem(matrix_t* mat, int row, int col, cint_t elem);

matrix_t* mat_mul(matrix_t* A, matrix_t* B);

matrix_t* mat_sum(matrix_t* A, matrix_t* B);

matrix_t* mat_pointwise_mul(matrix_t* A, matrix_t* B);

void display_mat(matrix_t* mat);

void free_mat(matrix_t** m_ptr);

#endif
