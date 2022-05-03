#include "matrix.h"
#include <stdlib.h>
#include <stdio.h>

// Initialize with arr or with 0 if no arr
matrix_t* create_mat(cint_t* arr, int rows, int cols){
    cint_t* new_arr = malloc(rows * cols * sizeof(cint_t));
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
                new_arr[i * cols + j] = arr[i * cols + j];
            }
            
        }
    }else{
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                new_arr[i * cols + j] = (cint_t){0};
            }
            
        }
    }
    ret->mat = new_arr;
    ret->col_size = cols;
    ret->row_size = rows;
    return ret;
}

matrix_t* duplicate_mat(matrix_t* mat){
    return create_mat(mat->mat, mat->row_size, mat->row_size);
}

int check_range(matrix_t* mat, int row, int col){
    return row >= 0 && row < mat->row_size &&
        col >= 0 && col < mat->col_size;
}

cint_t get_elem(matrix_t* mat, int row, int col){
    if(!check_range(mat, row, col)){
        printf("Invalid range for elem\n");
        exit(1);
    } 
    return mat->mat[row * mat->col_size + col];
}

void put_elem(matrix_t* mat, int row, int col, cint_t elem){
    if(!check_range(mat, row, col)){
        printf("Invalid range for elem\n");
        exit(1);
    } 
    mat->mat[row * mat->col_size + col] = elem;
}

matrix_t* mat_mul(matrix_t* A, matrix_t* B){
    if(A->col_size != B->row_size){
        printf("Matrices must have same inner rank\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = B->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            cint_t sum = {0};
            for (int k = 0; k < A->col_size; k++)
            {
                sum = add(sum, mul(get_elem(A, i, k), get_elem(B, k, j)));
            }
            
            put_elem(new_mat, i, j, sum); 
        }
        
    }
    return new_mat;
    
}

matrix_t* mat_sum(matrix_t* A, matrix_t* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        printf("Matrices must have same ranks\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            put_elem(new_mat, i, j, add(get_elem(A, i, j), get_elem(B, i, j)));
        }
        
    }
    return new_mat;
    
}

matrix_t* mat_pointwise_mul(matrix_t* A, matrix_t* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        printf("Matrices must have same ranks\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix_t* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            put_elem(new_mat, i, j, mul(get_elem(A, i, j), get_elem(B, i, j)));
        }
        
    }
    return new_mat;
    
}

void display_mat(matrix_t* mat){
    for (int i = 0; i < mat->row_size; i++)
    {
        printf(" ");
        for (int j = 0; j < mat->col_size; j++)
        {
            printf("%d ", get_elem(mat, i, j).x);
        }
        printf("\n");
    }
}

void free_mat(matrix_t** m_ptr){
    free((*m_ptr)->mat);
    free(*m_ptr);
    *m_ptr = 0;
}