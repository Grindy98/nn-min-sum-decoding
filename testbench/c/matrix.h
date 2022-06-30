#ifndef MATRIX
#define MATRIX

#include <stdint.h>
#define CINT_SIZE 8


typedef struct matrix_t{
    unsigned is_mod_two : 1;
    int row_size;
    int col_size;
    int64_t* mat;
} matrix_t;

matrix_t* create_mat(int64_t* arr, int rows, int cols, int is_mod_two);
matrix_t* duplicate_mat(matrix_t* mat, int is_mod_two);

int check_range(matrix_t* mat, int row, int col);
int64_t get_elem(matrix_t* mat, int row, int col);
void put_elem(matrix_t* mat, int row, int col, int64_t elem);

void mat_apply_saturation(matrix_t* A);

matrix_t* mat_extract(matrix_t* A, int row, int col);
matrix_t* mat_mul(matrix_t* A, matrix_t* B);
matrix_t* mat_sum(matrix_t* A, matrix_t* B);
matrix_t* mat_pointwise_mul(matrix_t* A, matrix_t* B);

void display_mat(matrix_t* mat);
void free_mat(matrix_t** m_ptr);

#endif
