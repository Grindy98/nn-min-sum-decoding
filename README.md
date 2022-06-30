*******************************************************************************
# General description of project

The project targets the development of an error correction scheme for parity
based codes using machine learning approaches. 

We aim for a custom deep 
neural network, based on the Tanner graph of the error correction code, 
using Min-Sum based algorithm in log domain. 

The previously trained neural
network will be implemented on a ZedBoard platform.

*******************************************************************************
# Description of project structure                        

The structure of the project is divided into five main parts:
- `data\` which contains the necessary data for the layers of the model
    (exported biases, adjacency matrices etc).

- `docs\` which contains a short report describing the development and 
    results of the trained neural network.

- `hardware\` which contains the verilog modules as well as a python script
    that generates the odd, even, and out layers.

- `model\` which contains the python modules and notebook needed to create
    the python model of the NOMS decoder.

- `testbench\` which contains:
    - `testbench\sv\`: the testbench module implemented in SystemVerilog, together
    with a `.tcl` script used to refresh the whole Vivado project structure.
    - `testbench\c\`: all the C files (and header files) used to emulate the decoder.
    `verilog_wrapper.c` defines all C library functions used within the testbench
    through the DPI-C interface.  

*******************************************************************************
# Steps to build and test project

## Python Setup

To install all the dependencies, simply run `pip install -r requirements.txt`

NOTE: After installation, Jupytext should also be available as an extension in
Jupyter Notebook (see File &rarr; Jupytext).

## Verilog Setup
1. Open Xilinx Vivado and create new project
2. Close Xilinx Vivado and open the folder where the project was created 
3. Copy the file named functions.tcl found in testbench/sv/ and change the 
first line to the repository path
4. Open the project using Vivado .xpr file
5. Check if the project was opened as expected by typing in the tcl console
pwd, otherwise change directory until the current folder is the folder where
the Vivado project is 
6. Type: source functions.tcl
7. Type: refresh
8. Type: simulate

*******************************************************************************
