@echo off
setlocal
cd /d %~dp0

call python codegen.py ../../data/adj_matrices.npz ../../data/biases.npy ../../data/generator.npy -p ../../data/params.json -o import_matrix_wrapper
