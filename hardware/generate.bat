@echo off
setlocal
cd /d %~dp0

call python verilog_gen.py -p ..\data\params.json -i ..\data\adj_matrices.npz ..\data\biases.npy -var_o variable_nodes -check_o check_nodes -lut_o lut_biases -out_o out_layer -vh_o ct.vh
