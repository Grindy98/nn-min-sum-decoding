#ifndef MATRIX
#define MATRIX

#define CINT_BITSIZE 4
#define CINT_MAX (~((~0u) << (CINT_BITSIZE-1)))
#define CINT_MIN (1u << (CINT_BITSIZE-1))

typedef struct cint_t{
    int x : CINT_BITSIZE;
} cint_t;


typedef struct matrix_t{
    unsigned is_mod_two : 1;
    int row_size;
    int col_size;
    cint_t* mat;
} matrix_t;


cint_t add(cint_t a, cint_t b);
cint_t sub(cint_t a, cint_t b);
cint_t mul(cint_t a, cint_t b);
cint_t mod_2(cint_t a);

matrix_t* create_mat(cint_t* arr, int rows, int cols, int is_mod_two);
matrix_t* duplicate_mat(matrix_t* mat, int is_mod_two);

int check_range(matrix_t* mat, int row, int col);
cint_t get_elem(matrix_t* mat, int row, int col);
void put_elem(matrix_t* mat, int row, int col, cint_t elem);

matrix_t* mat_mul(matrix_t* A, matrix_t* B);
matrix_t* mat_sum(matrix_t* A, matrix_t* B);
matrix_t* mat_pointwise_mul(matrix_t* A, matrix_t* B);

void display_mat(matrix_t* mat);
void free_mat(matrix_t** m_ptr);

#endif
