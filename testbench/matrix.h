#ifndef MATRIX
#define MATRIX

typedef struct matrix{
    int row_size;
    int col_size;
    int* mat;
} matrix;

matrix* create_mat(int* arr, int rows, int cols);

matrix* duplicate_mat(matrix* mat);

int check_range(matrix* mat, int row, int col);

int get_elem(matrix* mat, int row, int col);

void put_elem(matrix* mat, int row, int col, int elem);

matrix* mat_mul(matrix* A, matrix* B);

matrix* mat_sum(matrix* A, matrix* B);

matrix* mat_pointwise_mul(matrix* A, matrix* B);

void display_mat(matrix* mat);

void free_mat(matrix** m_ptr);

#endif
