INSTRUMENTORS_DIR=$(shell pwd)/instrumentors
TOP_DIR=$(shell pwd)/..
GDB_COMMANDS_DIR=$(ANALYSIS_DIR)/gdb-commands

ANALYSIS_CONFIG?=$(shell pwd)/pldi-short-config

all: instrumentors/stamp

instrumentors/stamp:
	@$(MAKE) -C instrumentors --file=Commands.mk
	touch $@

.SECONDEXPANSION:
results_trace/gcc/v1/singleton/gcc.graphml: $$(@D)/graph.part00 $$(@D)/graph.part01
	cat $(@D)/graph.part00 $(@D)/graph.part01 > $@

analyze-results: instrumentors/stamp results_trace/gcc/v1/singleton/gcc.graphml
	(\
    cd scripts && \
    rm -f errs && \
    ( EXTRA_CONFIG=$(ANALYSIS_CONFIG) ./run-analyze | tee -a /dev/tty ) >& errs && \
    cp errs ../$@ \
	)

clean:
	@$(MAKE) -C instrumentors --file=Commands.mk clean
	-rm -rf instrumentors/stamp analyze-results results_trace/gcc/v1/singleton/gcc.graphml
	-find results_trace -iregex '.*\.result.*' -exec rm -f {} \;

.DELETE_ON_ERROR:
