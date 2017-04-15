#!/usr/bin/make --file

TOOLS_DIR=$(shell pwd)/csi-cc/Tools
RESULTS_DIR=$(shell pwd)/results

# child Makefiles need these variables
export ANALYSIS_DIR := $(shell pwd)/csi-grissom
export PATH := $(ANALYSIS_DIR)/frontend:$(ANALYSIS_DIR)/analysis:/s/gcc-4.9.2/bin:/unsup/gdb-7.9/bin:/s/python-2.7.1/bin:/s/python-3.4.3/bin:/s/autoconf-2.69/bin:/usr/lib/jvm/java-1.8.0-oracle.x86_64/bin:/s/maven-3.3.3/bin:/usr/bin:/bin:$(PATH)
export PYTHONPATH := /p/csi/public/tools/networkx/1.10/install:$(ANALYSIS_DIR)/analysis:$(ANALYSIS_DIR)/analysis/csilibs/:/p/csi/public/tools/pyfst/install:/p/csi/public/tools/jpype/install:/p/csi/public/tools/z3/install/lib/python2.7/dist-packages:$(PYTHONPATH)

SHARED_RESULTS_DEPS := llvm/stamp csi-cc/stamp csi-grissom/stamp symbolicautomata/stamp

# parameters: results-target [extra-config]
define results-run
@$(MAKE) -C results --file=Commands.mk $(1) $(2)
endef

define results-run-ignore-dep
@$(MAKE) -C results --file=Commands.mk instrumentors/stamp;
$(call results-run,$(1),--assume-new=extract-results $(2))
endef

all: pldi-analyze

symbolicautomata/stamp:
	mvn clean install -f symbolicautomata/pom.xml
	touch $@

csi-grissom/stamp: symbolicautomata/stamp csi-cc/stamp
	@$(MAKE) --directory=$(@D) SVPA_LIB_DIR=`pwd`/symbolicautomata/SVPAlib CSI_CC=`pwd`/csi-cc/Release/csi-cc
	touch $@

llvm/stamp:
	@$(MAKE) --directory=$(@D) --file=Commands.mk
	touch $@

csi-cc/stamp: llvm/stamp
	scons --directory=$(@D) --jobs=`nproc` LLVM_CONFIG=`pwd`/llvm/install/bin/llvm-config test
	touch $@

analyze: $(SHARED_RESULTS_DEPS)
	$(call results-run,analyze-results)

re-analyze: $(SHARED_RESULTS_DEPS)
	rm -f results/analyze-results
	$(MAKE) analyze

paper-figures:
	./makeCSV.py results > results/summarize/csi-data.csv
	./makeCSV.py results -stack > results/summarize/stack-data.csv
	scons --directory=results/summarize subjects=`pwd`/subjects
	cp results/summarize/paper-figures $@

pldi-analyze: $(SHARED_RESULTS_DEPS)
ifdef MAX_MEMORY
	@read -p "Running with memory threshold: $(MAX_MEMORY) MB [Press any key]"
endif
	# similar to two runs of "re-analyze" but without the dependencies
	# hence, this target won't work outside of the PLDI 2017 artifact setup
	rm -f results/analyze-results results/csi-analyze-results
	@echo "====================================================================="
	@echo "=== Running analysis to gather \"stacks and call coverage\" results ==="
	@echo "====================================================================="
	$(call results-run-ignore-dep,analyze-results,STACK_ONLY=0)
	mv results/analyze-results results/csi-analyze-results
	@echo "========================================================"
	@echo "=== Running analysis to gather \"stacks only\" results ==="
	@echo "========================================================"
	$(call results-run-ignore-dep,analyze-results,STACK_ONLY=1)
	$(MAKE) paper-figures

smoke-test: $(SHARED_RESULTS_DEPS)
	# very quick run: only do tcas
	$(call results-run-ignore-dep,analyze-results,STACK_ONLY=1 ANALYSIS_CONFIG=$(RESULTS_DIR)/only-tcas-config)
	./makeCSV.py results -stack
	echo "Smoke test: OK!"

clean:
	rm -f csi-grissom/stamp llvm/stamp csi-cc/stamp symbolicautomata/stamp
	rm -f paper-figures results/csi-analyze-results
	scons --directory=csi-cc --clean LLVM_CONFIG=/bin/false
	scons --directory=results/summarize --clean
	@$(MAKE) -C csi-grissom clean
	@$(MAKE) -C llvm --file=Commands.mk clean
	@$(MAKE) -C results --file=Commands.mk clean
	mvn clean -f symbolicautomata/pom.xml

.PHONY: paper-figures
