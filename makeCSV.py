#!/usr/bin/env python

import os
import os.path
from argparse import ArgumentParser
from sys import stderr

SOLVERS = ["UTL", "FSA", "SVPA"]

def printOne(solver, app, version, fault, completed, timeout, memoryout, totaltime, yesCount, noCount, maybeCount):
  printable = "" + solver + "," + app + "," + version + "," + fault;
  for v in [completed, timeout, memoryout]:
    printable += "," + ("TRUE" if v else "FALSE");
  printable += "," + totaltime;
  for v in [yesCount, noCount, maybeCount]:
    printable += "," + (v if v != None else "");
  return(printable);
#end: printOne

def extractOneSolver(solver, path, fileToSearch):
  timeoutCount = 0;
  memoryoutCount = 0;
  completedCount = 0;

  for dirname, dirnames, filenames in os.walk(path):
    for filename in filenames:
      if(filename == fileToSearch):
        splitDir = dirname.split('/');
        fault = splitDir[-2];
        version = splitDir[-3];
        if(version[0] != "v"):
          print >> stderr, ("Invalid version");
          exit(1);
        #end if
        version = version[1:];
        app = splitDir[-4];

        timedOut = False;
        memedOut = False;
        completed = False;
        completedTime = None;
        failedTime = None;
        yesCount = None;
        noCount = None;
        maybeCount = None;

        with open(os.path.join(dirname, filename), 'r') as readMe:
          for line in readMe:
            if(line[:8] == "@TIMEOUT"):
              timedOut = True;
            elif(line[:10] == "@MEMORYOUT"):
              memedOut = True;
            elif(line[:13] == "@ANALYSISTIME"):
              completed = True;
              completedTime = line[13:].strip();
            elif(line[:12] == "@FAILURETIME"):
              failedTime = line[12:].strip();
            elif(line[:8] == "defYes ("):
              yesCount = line[8:].split()[0].strip();
            elif(line[:7] == "defNo ("):
              noCount = line[7:].split()[0].strip();
            elif(line[:7] == "maybe ("):
              maybeCount = line[7:].split()[0].strip();
          #end for
        #end with
        
        # check consistency
        if(failedTime == None and completedTime == None):
          print >> stderr, ("ERROR: run neither completed nor failed!");
          print >> stderr, (os.path.join(dirname, filename));
          exit(1);
        elif(failedTime != None and completedTime != None):
          print >> stderr, ("ERROR: run completed and failed!");
          print >> stderr, (os.path.join(dirname, filename));
          exit(1);
        elif(failedTime != None and not timedOut and not memedOut):
          print >> stderr, ("ERROR: failure with no time or memory out!");
          print >> stderr, (os.path.join(dirname, filename));
          exit(1);
        #end if

        print(printOne(solver, app, version, fault, \
                       completed, timedOut, \
                       False if timedOut else memedOut, \
                       (completedTime if completedTime != None else failedTime), \
                       yesCount, noCount, maybeCount));
      #end if
    #end for
  #end for

  return(str(timeoutCount) + " " + str(memoryoutCount) + " " + str(completedCount));
#end: extractOneSolver

def extractCSV(path, stackOnly):
  print("Solver,App,Version,Fault,Completed,Timeout,Memoryout,AnalysisTime,Yes,No,Maybe")
  for solver in SOLVERS:
    extractOneSolver(solver, path, "inter." + solver + ".result" + \
                                   (".stack" if stackOnly else ""));
#end: extractCSV

def parseArguments():
  parser = ArgumentParser(prog="makeCSV",
              description="Create the result CSV file from a result directory");
  parser.add_argument("directory", help="Path to the result directory.");
  parser.add_argument("-stack", "--stack", action="store_true",
                      dest="stack", default=False,
                      help="Look for \"stack-only\" analysis results.");
  return(parser.parse_args());
#end: parseArguments

def main():
  args = parseArguments();

  extractCSV(args.directory, args.stack);
#end: main

if __name__ == '__main__' :
  main()
