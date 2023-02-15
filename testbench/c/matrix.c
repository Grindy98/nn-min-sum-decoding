#include "matrix.h"
#include <stdlib.h>
#include "print.h"

// Initialize with arr or with 0 if no arr
matrix_t* create_mat(int64_t* arr, int rows, int cols, int is_mod_two){
    int64_t* new_arr = malloc(rows * cols * sizeof(int64_t));
    if(new_arr == NULL){
        exit(1);
    }
    matrix_t* ret = malloc(sizeof(matrix_t));
    if(ret == NULL){
        exit(1);
    }
    if (arr){
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                int64_t elem = arr[i * cols + j];
                new_arr[i * cols + j] = is_mod_two ? (elem % 2) : elem;
            }
            
        }
    }else{
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                new_arr[i * cols + j] = 0;
            }
            
        }
    }
    ret->mat = new_arr;
    ret->col_size = cols;
    ret->row_size = rows;
    ret->is_mod_two = (is_mod_two != 0);
    return ret;
}

matrix_t* duplicate_mat(matrix_t* mat, int is_mod_two){
    return create_mat(mat->mat, mat->row_size, mat->col_size, is_mod_two);
}

int check_range(matrix_t* mat, int row, int col){
    return row >= 0 && row < mat->row_size &&
        col >= 0 && col < mat->col_size;
}

int64_t get_elem(matrix_t* mat, int row, int col){
    if(!check_range(mat, row, col)){
        custom_print("Invalid range for elem\n");
        exit(1);
    } 
    return mat->mat[row * mat->col_size + col];
}

void put_elem(matrix_t* mat, int row, int col, int64_t elem){
    if(!check_range(mat, row, col)){
        custom_print("Invalid range for elem\n");
        exit(1);
    } 
    mat->mat[row * mat->col_size + col] = mat->is_mod_two ?
        ((2 + (elem % 2)) % 2) : elem;
}

void mat_apply_saturation(matrix_t* A){
    int64_t maxsize = 1;
    maxsize <<= CINT_SIZE - 1;
    maxsize -= 1;

    int64_t minsize = -1;
    minsize <<= CINT_SIZE - 1;

    for (int i = 0; i < A->row_size; i++)
    {
        for (int j = 0; j < A->col_size; j++)
        {
            int64_t elem = get_elem(A, i, j);
            elem = elem > maxsize ? maxsize : elem;
            elem = elem < minsize ? minsize : elem;
            put_elem(A, i, j, elem);
        }
        
    }
}

matrix_t* mat_extract(matrix_t* A, int row, int col){
    if(!check_range(A, row == -1 ? 0 : row, col == -1 ? 0 : col)){
        custom_print("Invalid range for row/col extraction\n");
        exit(1);
    }

    matrix_t* new_mat = create_mat(NULL, row == -1 ? A->row_size : 1, col == -1 ? A->col_size : 1, A->is_mod_two);
    for(int i = 0; i < A->row_size; i++){
        if(row != -1 && row != i){
            continue;
        }
        int ii = row == -1 ? i : 0;
        for(int j = 0; j < A->col_size; j++){
            if(col != -1 && col != j){
                continue;
            }
            int jj = col == -1 ? j : 0;
            put_elem(new_mat, ii, jj, get_elem(A, i, j));
        }
    }
    return new_mat;
}

matrix_t* mat_mul(matrix_t* A, matrix_t* B){
    if(A->col_size != B->row_size){
        custom_print("Matrices must have same inner rank: %d != %d\n",
            A->col_size, B->row_size);
        exit(1);
    }
    // If both matrices are mod two, resul is also mod two
    int mod_two_flag = A->is_mod_two && B->is_mod_two;

    int new_row = A->row_size;
    int new_col = B->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col, mod_two_flag);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            int64_t sum = 0;
            for (int k = 0; k < A->col_size; k++)
            {
                sum += get_elem(A, i, k) * get_elem(B, k, j);
                sum = mod_two_flag ? (sum % 2) : sum;
            }
            
            put_elem(new_mat, i, j, sum); 
        }
        
    }
    return new_mat;
    
}

matrix_t* mat_sum(matrix_t* A, matrix_t* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        custom_print("Matrices must have same ranks: (%d, %d) != (%d, %d)\n",
            A->row_size, A->col_size, B->row_size, B->col_size);
        exit(1);
    }
    // If both matrices are mod two, resul is also mod two
    int mod_two_flag = A->is_mod_two && B->is_mod_two;

    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col, mod_two_flag);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            int64_t new_sum = get_elem(A, i, j) + get_elem(B, i, j);
            put_elem(new_mat, i, j, mod_two_flag ? (new_sum % 2) : new_sum);
        }
        
    }
    return new_mat;
    
}

matrix_t* mat_pointwise_mul(matrix_t* A, matrix_t* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        custom_print("Matrices must have same ranks: (%d, %d) != (%d, %d)\n",
            A->row_size, A->col_size, B->row_size, B->col_size);
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col, A->is_mod_two && B->is_mod_two);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            put_elem(new_mat, i, j, get_elem(A, i, j) * get_elem(B, i, j));
        }
        
    }
    return new_mat;
    
}

void display_mat(matrix_t* mat){
    for (int i = 0; i < mat->row_size; i++)
    {
        custom_print(" ");
        for (int j = 0; j < mat->col_size; j++)
        {
            custom_print("%ld ", get_elem(mat, i, j));
        }
        custom_print("\n");
    }
}

void free_mat(matrix_t** m_ptr){
    free((*m_ptr)->mat);
    free(*m_ptr);
    *m_ptr = 0;
}