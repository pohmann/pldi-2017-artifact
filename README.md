# Control-Flow Recovery from Partial Failure Reports

This artifact contains a virtual machine (pldi-2017.ova) with all necessary
dependencies installed for re-running the experiments from the paper
"Control-Flow Recovery from Partial Failure Reports", published in
PDLI 2017.  The VM also has necessary scripts to run `csi-cc` instrumentation
and the analyses described in the paper on arbitrary C programs.


## Logging in to the Virtual Machine

First, import the virtual machine into a virtual machine manager, such as
VirtualBox.  You can log into the machine with the following credentials:
```
User:     vagrant
Password: vagrant
```

The machine is currently set up to use 12 processors and 32GB of RAM.  You can
edit the number of processors as appropriate for your machine's CPU.  (We
recommend 4 processors if possible, though 2 should be sufficient.)  If you
intend to reproduce the experiments from the paper, we recommend that you do not
decrease the RAM allocation below 32GB.  However, if the host machine does not
have 32GB of RAM, then the user will need to reduce the memory allocation for
the virtual machine.  This will be sufficient for testing our analysis directly
(see the
[Running Analysis on Arbitrary Programs](#running-analysis-on-arbitrary-programs)
section), but may not be suitable for reproducing paper experiments, because
additional test subjects may run out of time or memory.


## Smoke Test

Users should begin by running a "smoke-test" to verify that the current setup is
working correctly before running the full set of experiments. To run the test,
you can run:
```
cd /vagrant
make smoke-test
```
The test should take approximately 10 minutes to run, and report "Smoke test:
OK!" when finished.


## To Reproduce Paper Results

### Pre-Selected Application Set

In brief, to reproduce a selection of the paper results, run:
```
cd /vagrant
make pldi-analyze
```
This will run the analysis on a pre-selected set of evaluated applications
(print_tokens, print_tokens2, schedule, schedule2, and ccrypt) that are
expected to complete in 24–48 hours.

Unless you:
* want to do additional tweaking of experiments, or
* reduced your virtual machine's memory below 32GB,
skip ahead to the [Comparing Results](#comparing-results) section.

### Running a Different Set of Applications

To edit which applications are run, edit or create a configuration file.  By
default, `make` uses the configuration file `/vagrant/results/pldi-short-config`.
To use a different configuration file, run `make` as follows:
```
make pldi-analyze ANALYSIS_CONFIG=/path/to/config/file
```
The repository contains a configuration file, `/vagrant/results/analysis-config`,
that configures the analysis to run every application from the paper.  Running
the analysis for all failures will take a substantial amount of time: on the
order of 1-2 weeks.  The time duration is dominated by larger applications with
many evaluated failures, such as space, sed, and flex.

### Reduced Memory Threshold

If the virtual machine is allocated less than 32GB of RAM, users should also
reduce the memory threshold below 32GB for running out of memory during the
experiments.  To do so, use the environment variable `MAX_MEMORY`, which should
give the memory-out limit in MB (matching the memory allocated to the VM).  So,
for example, to run the default selection of applications with the memory limit
set to 16GB, you can run:
```
cd /vagrant
make pldi-analyze MAX_MEMORY=16384
```

However, note that we *do not recommend* this if using 32GB of RAM is possible.
Changing the memory threshold for the experiments will result in more subjects
exceeding the memory threshold than in our original paper experiments.  Hence,
the results obtained in this manner will very likely not as closely match those
from our original experiments.  We have not tested our artifact with
`MAX_MEMORY` set below 5GB.

### Comparing Results

A run of `make pldi-analyze` will generate a result file
`/vagrant/paper-figures`.  This file contains the summarized result data in the
same format as all tables and figures from section 6 of the PLDI paper.  Raw
result data is also generated in `.csv` format at:
```
results/summarize/stack-data.csv
results/summarize/csi-data.csv
```
for stack-only and stack-plus-call-coverage results respectively.  A number of
other intermediate `.csv` files for the tables in `/vagrant/paper-figures` are
also generated in this directory.

While we expect that results should be very similar to those in the paper, it is
possible that a fresh run will yield more time-out analysis runs than reported
in the paper and slightly different ratios for relative analysis run times
(as given in figures 11 and 13 of the paper).  This is because the original
experiments were performed on a bare-metal machine, while the artifact runs in a
virtual machine.  We expect the effects on results to be minimal, though we have
observed longer running times in our own testing.


## Running Analysis on Arbitrary Programs

The artifact also contains the necessary scripts to run the analysis on
arbitrary programs.  There are two ways to do so:

* Run the analysis, `csi-grissom`, directly on extracted failure data and a CFG
  file
* An automated script, `do-csi-analysis`, that extracts the necessary
  information for running the analysis on an executable compiled with the
  `csi-cc` instrumenting compiler, and a core dump generated from that
  executable

Each of the two methods are explained separately, along with when and how one
might use them.  In all cases, the analysis will run one query for each basic
block in the program, and output the Yes, No, and Maybe sets as discussed in
section 6 of the PLDI paper.

### Running Analysis Directly on Subjects with `csi-grissom`

To run analysis for a single failure, the basic command is:
```
csi-grissom -json path_to_json path_to_graphml
```
Here, the JSON file is the extracted failure data for the failing run, and the
GraphML file is the control-flow graph of the program.

The `csi-grissom` script takes a number of arguments to configure which solver
is run (UTL, FSA, or SVPA) and how results are formatted.  Run
```
csi-grissom --help
```
for the full listing of options.  Some commonly useful options include:

* `-first <UTL,FSA,SVPA>` indicates which solver to run. (default: UTL)
* `-result-style <none,compact,full,csiclipse,standard>` indicates how to
  display the results.  The two most useful options are `compact`, which simply
  displays the sizes of the Yes, No, and Maybe sets, and `standard`, which
  displays the list of lines in each file that have at least one expression
  marked as Yes, No, and Maybe. (default: compact)
* `-stackonly` tells the analysis to ignore all failure data except the crashing
  stack trace (e.g., ignore `csi-cc` call coverage data).

less common options that may be useful include:

* `-second <UTL,FSA,SVPA,None>` indicates a second solver to run (if any) whose
  output will be compared to the first solver.  This is useful to verify that
  all solvers produce expected results. (default: None)
* `-compare <eq,gt,lt>` indicates how the analysis should compare the results of
  the first and second solvers.  If `eq`, they should produce exactly the same
  Yes, No, and Maybe sets.  If `gt`, the first solver is expected to be more
  precise, and should classify no less statements as Yes and/or No than the
  second solver (i.e., it's Maybe set should be a subset of the second solver's
  Maybe set).  If `lt`, the second solver should be more precise.

For example, the application `gzip` is not part of the pre-selected set of
experiments.  Suppose one would like to run analysis on the extracted failure
data in
`/vagrant/results/results_trace/gzip/v1/FAULTY_F_KL_2/9-trace/data.json`.  The
following command would do so:
```
csi-grissom -json /vagrant/results/results_trace/gzip/v1/FAULTY_F_KL_2/9-trace/data.json /vagrant/results/results_trace/gzip/v1/FAULTY_F_KL_2/gzip.graphml
```
All extracted failure data from the original experiments is contained within the
`/vagrant/results/results_trace` directory, with subdirectories for each
application, version, bug, and individual failing test case respectively.  The
above command runs the analysis on extracted failure data for the application
`gzip`, version `1`, with the seeded fault `FAULTY_F_KL_2`, on test case `9`.
The failure data itself is contained within the `data.json` file, while
`gzip.grahml` contains the program's control-flow graph. Note that this command
will not set any timeout or kill the process when it exceeds any memory
threshold, as it simply runs the analysis program directly.

### Running Analysis on an Executable and Core Dump

The script `do-csi-analysis` takes an executable file and a core dump (produced
from a failing run of that executable) as input, extracts the failure data from
the core dump, and runs `csi-grissom` on the extracted data.  The basic usage is
```
do-csi-analysis executable corefile
```

The script supports a number of options, and the full list is available by
running:
```
do-csi-analysis --help
```
The `-solver` and `-result-style` options are identical to those from
`csi-grissom`, as described above.  The `-save-temps` option instructs the
solver to not use a temporary directory, and instead store extracted failure
data in a new subdirectory of `cwd`.  The `-debug` flag allows all output to
flow directly from `csi-grissom` to the user, rather than hiding progress
updates and internal log messages printed by `csi-grissom`.

Note that the executable *must* be produced by the `csi-cc` instrumenting C
compiler.  The `csi-cc` compiler is extensively documented in
`/vagrant/csi-cc/doc/`.  We recommend the following command to compile for
testing:
```
csi-cc --trace=/vagrant/csi-cc/schemas/cc.schema -csi-opt=2 -opt-style=simple my_file.c
```
This command compiles `my_file.c` with optimized call-site coverage
instrumentation, precisely as done for the experiments in section 6 of the PLDI
paper.  Note that `csi-cc` is a near drop-in replacement for `gcc`, so it also
nearly all standard `gcc` options (such as `-c`).

The provided artifact machine is already configured to produce core dumps for
failing native applications (e.g., when calling `abort()` or causing a
segmentation fault).  If the application `a.out` (compiled and linked by
`csi-cc`) produced file `core.123` from a failing run, a basic launch of the
analysis would look like:
```
do-csi-analysis a.out core.123
```
Note that this command will not set any timeout or kill the process when it
exceeds any memory threshold, as it simply runs the analysis program directly.


## If Something Goes Wrong

We hope there are no issues with our artifact.  However, if a problem does
arise, the most useful information for us to debug the issue includes any
output from the failed command, as well as the following files:
```
/vagrant/results/scripts/errs
/vagrant/results/analyze-results
```
Please send failure reports to Peter Ohmann at <ohmann@cs.wisc.edu>.
