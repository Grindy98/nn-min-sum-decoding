# CONSTANT
set GIT_REPO_PATH D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding

proc ref {} {
	global GIT_REPO_PATH
	
	#Clean work
	vdel -all
	vlib work
	vmap work work
	
	# Regenerate all code files
	puts [exec ${GIT_REPO_PATH}/testbench/sim/globalgen.bat]
	
	puts "------------- C COMPILE -------------------"
	vlog -sv -dpiheader dpiheader.h -ccflags "-std=c99" -f ${GIT_REPO_PATH}/testbench/sim/simfiles_c.f
}

proc comp {} {
	global GIT_REPO_PATH
	puts "-------------- COMPILE --------------------"
	vlog -sv -f ${GIT_REPO_PATH}/testbench/sim/simfiles_v.f
}

proc sim {} {
	vsim work.tb
	do wave.do
	
	run 10us
}
