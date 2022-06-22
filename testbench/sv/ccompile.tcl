 proc try {script args} {
    upvar 1 try___msg msg try___opts opts
    if {[llength $args]!=0 && [llength $args]!=2} {
       return -code error "wrong \# args: should be \"try script ?finally script?\""
    }
    if {[llength $args] == 2} {
       if {[lindex $args 0] ne "finally"} {
          return -code error "mis-spelt \"finally\" keyword"
       }
    }
    set code [uplevel 1 [list catch $script try___msg try___opts]]
    if {[llength $args] == 2} {
       uplevel 1 [lindex $args 1]
    }
    if {$code} {
       dict incr opts -level 1
       return -options $opts $msg
    }
    return $msg
 }

set orig_dir [pwd]
try {
	set src_dir "D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding/testbench/c"
	# Generate c import_matrix file
	exec ${src_dir}/generate.bat
	
	set proj_name [current_project]
	set proj_path [get_property DIRECTORY [current_project]]
	cd ${proj_path}

	if {[catch {file delete -force "${proj_path}/${proj_name}.sim"} errmsg]} {
		puts "ErrorMsg: $errmsg"
		puts "ErrorCode: $errorCode"
		puts "ErrorInfo:\n$errorInfo\n"
	}
	set path_work "${proj_path}/${proj_name}.sim/sim_1/behav/xsim"
	puts [file normalize "."]
	puts [file normalize ${proj_path}]
	if {[file normalize "."] != [file normalize ${proj_path}]} {
		puts "--------------------PATH WRONG---------------------"
		error "path" "Paths don't match" 1 
	}

	file mkdir ${path_work}
	puts "--------------------C COMPILE---------------------"
	if {[glob -nocomplain -d $src_dir *.c] != ""} {
		puts "Compiling C files"
		if {[catch {exec xsc {*}[glob -d $src_dir *.c] -v} errmsg]} {
		   puts "ErrorMsg: $errmsg"
		   puts "ErrorCode: $errorCode"
		   puts "ErrorInfo:\n$errorInfo\n"
		}
		puts [file copy -force ./xsim.dir/work/xsc/dpi.a ${path_work}/dpi.a] 
		
	}

} finally {
	puts ${orig_dir}
	cd ${orig_dir}
	puts "-------------------------DONE------------------------"
}

