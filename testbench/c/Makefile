CXX = gcc
CXX_FLAGS = -Wall -g

# Final binary
BIN = testbench
# Put all auto generated stuff to this build dir.
BUILD_DIR = ./build

# List of all .c source files.
C_RAW = test.c $(wildcard *.c) import_matrix_wrapper.c
C = ${filter-out verilog_wrapper.c, ${C_RAW}}

# All .o files go to build dir.
OBJ = $(C:%.c=$(BUILD_DIR)/%.o)
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)

# Default target named after the binary.
$(BIN) : $(BUILD_DIR)/$(BIN)

# Actual target of the binary - depends on all .o files.
$(BUILD_DIR)/$(BIN) : $(OBJ)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) $^ -o $@

# Include all .d files
-include $(DEP)

# Build target for every single object file.
# The potential dependency on header files is covered
# by calling `-include $(DEP)`.
$(BUILD_DIR)/%.o : %.c
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -c $< -o $@

# Specific build targets
import_matrix_wrapper.c : ../../data/adj_matrices.npz ../../data/biases.npy ../../data/generator.npy codegen.py
	python3 codegen.py ../../data/adj_matrices.npz ../../data/biases.npy ../../data/generator.npy -p ../../data/params.json -o import_matrix_wrapper

.PHONY : clean
clean :
	-rm -f $(BUILD_DIR)/$(BIN) $(OBJ) $(DEP)