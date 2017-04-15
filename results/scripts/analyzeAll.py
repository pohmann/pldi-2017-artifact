#!/usr/bin/env python

from grissom import solve
import glob
import os
import os.path
import random
import resource
import signal
from argparse import ArgumentParser
from sys import stdout, stderr, argv
import time

from jpype import JavaException

RANDOM_SEED = 2132017;

SOLVERS = ["UTL", "FSA", "SVPA"]

def cpu_handler(signum, frame):
  assert(signum == signal.SIGXCPU);
  print >> stderr, ("ERROR: timeout error (SIGXCPU)");
  print >> stderr, ("@TIMEOUT");
  exit(1);
#end: cpu_handler

def mem_handler(signum, frame):
  if(signum == signal.SIGABRT):
    print >> stderr, ("THAT'S AN ABRT SIGNAL!!!");
  elif(signum == signal.SIGTERM):
    print >> stderr, ("THAT'S A TERM SIGNAL!!");
  else:
    print >> stderr, ("GOT SOMETHING ELSE: " + str(signum));
  #assert(signum == signal.SIGSEGV);
  print >> stderr, ("ERROR: memoryout error (ENOMEM)");
  print >> stderr, ("@MEMORYOUT");
  exit(1);
#end: mem_handler

def analyzeOne(solver, dirname, stackOnly):
  resultPath = os.path.join(dirname, "inter." + solver + ".result" + \
                            (".stack" if stackOnly else ""));

  # maxMemory is in MegaBytes
  # maxTime is in Seconds
  try:
    maxMemory = int(os.environ.get("MAX_MEMORY", 32768));
    maxMemory = max(maxMemory, 1024);
  except:
    maxMemory = 32768;
  try:
    maxTime = int(os.environ.get("MAX_TIME", 10800));
    maxTime = max(maxTime, 900);
  except:
    maxTime = 10800;

  signal.signal(signal.SIGALRM, lambda x, y: None);
  signal.signal(signal.SIGCHLD, lambda x, y: None);

  pid = os.fork();
  if(pid != 0):
    # in the parent: just wait for the child to finish or time/memory out
    # i.e., we still only run one analysis instance at a time
    startingT = time.time();
    #os.waitpid(pid, 0);
    while(True):
      (childPid, childExitStatus, childRUse) = os.wait4(pid, os.WNOHANG);
      if(childPid != 0):
        break;
      elif(time.time() - startingT > maxTime + 600):
        print >> stderr, ("Killing child who missed timeout signal");
        os.kill(pid, signal.SIGKILL);
        (childPid, childExitStatus, childRUse) = os.wait4(pid, 0);
        break;
      #end if
      signal.alarm(30);
      signal.pause();
      signal.alarm(0);
    #end while
    if(childExitStatus != 0):
      with open(resultPath, 'a') as resultFile:
        print >> resultFile, ("\n@FAILURETIME %0.3f" % (time.time() - startingT));
        foundProblem = False;
        if(childRUse.ru_utime + childRUse.ru_stime >= maxTime - 100):
          foundProblem = True;
          print >> resultFile, ("ERROR: timeout error final obs");
          print >> resultFile, ("@TIMEOUT");
        if(childRUse.ru_maxrss >= int(maxMemory * 0.625 * 1024)):
          foundProblem = True;
          print >> resultFile, ("ERROR: memoryout error final obs");
          print >> resultFile, ("@MEMORYOUT");
        if(not foundProblem):
          print >> resultFile, ("ERROR: unknown non-zero exit status");
          print >> resultFile, ("@UNKNOWN");
        #end if
      #end with
    #end if
    print >> stderr, ("Child rusage: " + str((childPid, childExitStatus, childRUse)));
    print >> stderr, ("That one took %0.3f" % (time.time() - startingT));
  else:
    # sadly, these all do NOTHING
    # resource.setrlimit(resource.RLIMIT_RSS, (10, 10))
    # resource.setrlimit(resource.RLIMIT_STACK, (100, 100))
    # resource.setrlimit(resource.RLIMIT_DATA, (100, 100))

    # don't dump core files; kill after 3 hours or using maxMemory GB of memory
    # NOTE: this is GB of address space (not RSS) due to OS limitations
    resource.setrlimit(resource.RLIMIT_CORE, (0,0));
    resource.setrlimit(resource.RLIMIT_CPU, (maxTime, maxTime + 60));
    signal.signal(signal.SIGXCPU, cpu_handler);
    if(solver not in ("SVPA", "Pexpect")):
      memLimitInBytes = int(maxMemory * 0.78125 * 1048576);
      resource.setrlimit(resource.RLIMIT_AS, (memLimitInBytes, memLimitInBytes));
    signal.signal(signal.SIGABRT, mem_handler);
    signal.signal(signal.SIGTERM, mem_handler);
    signal.signal(signal.SIGSEGV, mem_handler);

    retcode = -1;
    try:
      os.chdir(dirname);
      pathToOpen = "inter." + solver + ".result" + (".stack" if stackOnly else "");
      with open(pathToOpen, 'w') as resultFile:
        stdout.flush();
        stderr.flush();
        os.dup2(resultFile.fileno(), stdout.fileno());
        os.dup2(resultFile.fileno(), stderr.fileno());

        # find necessary input files via glob
        inGraphFile = glob.glob("../*.graphml");
        if(len(inGraphFile) != 1):
          print >> stderr, ("ERROR: wrong number of graphml files");
          print >> stderr, str(inGraphFile);
          print >> stderr, ("@ERROR");
          exit(1);
        #end if
        inGraphFile = inGraphFile[0];

        startTime = time.time();
        retcode = solve([inGraphFile, \
                         "--json=./data.json", \
                         "--first=" + solver, \
                         "--second=None"] + \
                        (["-stackonly"] if stackOnly else []));
        print("\n@ANALYSISTIME %0.3f" % (time.time() - startTime));
      #end with
    except MemoryError:
      print >> stderr, ("ERROR: memoryout error (PYTHON NOMEM)");
      print >> stderr, ("@MEMORYOUT");
      exit(1);
    except JavaException as caughtException:
      if("OutOfMemoryError" in str(caughtException.javaClass())):
        print >> stderr, ("ERROR: memoryout error (JAVA NOMEM)");
        print >> stderr, ("@MEMORYOUT");
        exit(1);
      else:
        print >> stderr, ("ERROR: some other kind of Java exception!");
        print >> stderr, caughtException.message();
        print >> stderr, caughtException.stacktrace();
        exit(1);
      #end if
    #end try

    # child (analysis run) should *always* exit; *never* return
    exit(0);
  #end if
#end: analyzeOne

def analyze(path, stackOnly):
  dirOptions = [];
  for dirname, dirnames, filenames in os.walk(path):
    for filename in filenames:
      if(filename == "data.json"):
        dirOptions.append(dirname);
        break;
      #end if
    #end for
  #end for

  numOptions = len(dirOptions);
  didOne = (numOptions > 0);
  if(didOne):
    random.seed(RANDOM_SEED);
    chosenDir = sorted(dirOptions)[random.randint(0, numOptions-1)];
    print >> stderr, ("Analyzing (currently interprocedural only): " + chosenDir);
    for solver in SOLVERS:
      analyzeOne(solver, chosenDir, stackOnly);
  #end if

  print >> stderr, ("Did " + ("1" if didOne else "0") + " analysis runs.");
#end: analyze

def clean_old(path, stackOnly):
  suffix = ".result" + (".stack" if stackOnly else "");
  resultFiles = ["inter."+solver+suffix for solver in SOLVERS];
  for dirname, dirnames, filenames in os.walk(path):
    for filename in filenames:
      if(filename in resultFiles):
        os.remove(os.path.join(dirname, filename));
#end: clean_old

def parseArguments():
  parser = ArgumentParser(prog="analyzeAll",
              description="Look through subdirectories of the specified " + \
                          "directory for json input data to run CSI " + \
                          "analysis.  Currently, only run analysis exactly " + \
                          "*once* for the directory (since the analysis " + \
                          "only times out at 3 hours).");
  parser.add_argument("directory", help="Path to the directory to analyze. " + \
                                        "(It will be recursively searched " + \
                                        "for data.json files.)");
  parser.add_argument("-stack", "--stack", action="store_true",
                      dest="stack", default=False,
                      help="Use only the stack information from data.json " + \
                           "files.  (I.e., ignore coverage data there.)");
  return(parser.parse_args());
#end: parseArguments

def main():
  args = parseArguments();

  clean_old(args.directory, args.stack);

  analyze(args.directory, args.stack);
#end: main

if __name__ == '__main__' :
  main()
