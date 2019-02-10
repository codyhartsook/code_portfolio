#!/usr/bin/perl
# Cody Hartsook chartsoo@ucsc.edu

# Assignment 4:
# perl implementation of a subset of gmake

# synopsis: pmake [-d] [target]
#           pmake

# Makefile must be present in the cwd

use strict;
use warnings;

use POSIX qw(strftime);

my $EXITCODE = 0;
our @gla;

# read Makefile
#######################################################################
sub parse_dep ($) {
   my ($line) = @_;
   return undef unless $line =~ m/^(\S+)\s*:\s*(.*?)\s*$/;
   my ($target, $dependency) = ($1, $2);
   my @dependencies = split m/\s+/, $dependency;
   return $target, \@dependencies;
}

my $filename = 'Makefile';
open(my $fh, '<:encoding(UTF-8)', $filename)
  or die "Could not open file '$filename' $!\n";

my %targets; # hash of dependecies and cmds
our %macros;  # hash of macros
my @first;

my $prevTarget = '';
while (my $row = <$fh>) {
   chomp $row;
   
   my $char = substr $row, 0, 1;
   if ($char eq "#"){  # match #, ignore line
      $row = <$fh>;
   }

   elsif ($row =~ m[\t]){
      my @line = split('\t', $row);
      my $cmd = $line[1];
      my $c = $targets{$prevTarget}->[1];
      my @commands = ();
      
      if (not $c){ 
         push @commands, $cmd;
         $targets{$prevTarget}->[1] = \@commands;
      }
      else {
         push $c, $cmd;
      }
   }

   elsif ($row =~ m[=]){ # match =, store macro
      my @elements = split(' = ', $row);
      # remove whitespace from [0]
      $elements[0] =~ s/\s+$//;
      $macros {$elements[0]} = $elements[1]; #insert macros into table
   }

   elsif ($row =~ m[:]){ #match :, inset target, dep, and cmd
      # get the target
      my ($target, $deps) = parse_dep $row;
      $prevTarget = $target;
      push @first, $target;

      
      my $d = $targets{$target}->[0];
      if (not $d){
         my $cmd = undef; #placeholder cmd
         $targets{$target} = [$deps, $cmd];
      }
      else { # push new dependency into array of deps 
         foreach my $newdep (@$deps){
            push $d, $newdep;
         }
      }
   }
}

# for debugging #######################################################
sub print_macros ($) { 
   my @macs = keys %macros;
   for my $ms (@macs){
      print "$ms -> $macros{$ms}\n";
   }
}

sub print_targets ($) {
   for my $target (keys %targets) {
      print "\"$target\"";
      my $deps = $targets{$target}->[0];
      if (not @$deps) {
         print " has no dependencies";
      }else {
         print " depends on";
         print " \"$_\"" for @$deps;
      }
      print "\n";
   }
}

# for time stamping ###################################################
sub mtime ($) {
   my ($filename) = @_;
   my @stat = stat $filename;
   return @stat ? $stat[9] : undef;
}

sub hashref {
   my ($mac) = @_;
   my @split;
   
   if ($mac =~ m[\$]){              # is this a macro
      $mac =~ m/(\w+)/;             # extract macro
      my $nested = $1;
      my $deref = $macros{$nested}; # hash reference macro
      @split = split('\s', $deref); # see if there are multiples
      $mac = $deref;

   }
   else{ @split = split('\s', $mac); }
      
   my $size = @split;
   if ($size > 1){
      foreach my $var (@split){
         hashref ($var);
      }
   }

   else{ # just a file, compare dates
      push @gla, $mac;
      return $mac;
   }
}

sub handle_macros {
   my ($arg) = @_;
   @gla = ();
   my @local;

   hashref($arg);
   @local = @gla;
   @gla = ();
   return @local;
}

sub sys ($) { # parse flags and execute line
   my ($cmd) = @_;
   my $neg_flag = 0;
   my $char = substr $cmd, 0, 1;
   my $len = length $cmd;

   if ($char eq ' '){ # remove leading spaces
      $cmd = substr $cmd, 1, $len;
      $len --;
      $char = substr $cmd, 0, 1;
   }

   if ($char eq '@'){ # echo silent
      $cmd = substr $cmd, 1, $len;
   }
   else {
      if ($char eq '-'){ # dont exit if child fails
         $neg_flag = 1;
         $cmd = substr $cmd, 1, $len;
         $len --;
         $char = substr $cmd, 0, 1;
         if ($char eq ' ') { $cmd = substr $cmd, 1, $len; }
      }
      if ($cmd =~ m/\n/) { print "$cmd"; }
      else { print "$cmd\n"; }
   }
   system($cmd);
   my $term_signal = $? & 0x7F;
   my $exit_status = ($? >> 8) & 0xFF;
   if ($exit_status > 0 && $neg_flag == 0){ 
      print "child exit exit_status = $exit_status\n";
      exit 1;
   }
}

sub rec_exc ($) { # prepare command for execution
   my ($command) = @_;
   my $sig;
   
   #print "cmd: $command\n";
   if ($command =~ m[\$]){ # if there is a macro in command
      
      my @split = split ('\s', $command);
      my $cmd = '';
      #my @temp = @arr;
      
      foreach my $arg (@split){
         if ($arg =~ m[\$]){
            my @arr = handle_macros ($arg);
            
            foreach my $arg2 (@arr){
               $arg2 = ' ' . $arg2;
               $cmd = $cmd . $arg2;
            }
         }
         else { 
            $arg = ' ' . $arg;
            $cmd = $cmd . $arg; 
         }
      }
      sys $cmd; # execute cmd
   }
   else { # no macro, execute
      sys $command; #execute command
   }
}

sub execute ($){
   my ($command) = @_;
   
   if (ref ($command) eq 'ARRAY') {
      foreach my $cm (@$command){
         print "cmd: $cm\n";
         if ($cm =~ m[:]){
            my @sp = split('\:', $cm);
            print "$sp[0]:";
            my $newc = $sp[1];
            rec_exc $newc;
         } else { rec_exc $cm; }
      }
   }
   else { rec_exc $command; }
}

# macros are stored, directed graph created
# parse cmd line ops and targets
#######################################################################
$0 =~ s|^(.*/)?([^/]+)/*$|$2|;
END{ exit $EXITCODE; }
sub note(@) { print STDERR "$0: @_"; };
$SIG{'__WARN__'} = sub { note @_; $EXITCODE = 1; };
$SIG{'__DIE__'} = sub { warn @_; exit; };

use Getopt::Std;
my %OPTS;
my $debug;
getopts ("abcdh", \%OPTS);
my $d = 'd';
$debug = $OPTS{'d'};
if ($debug){
   print "debug option was set\n";
   print "\n";

   for my $target (keys %targets) {
      print "\"$target\"";
      my $deps = $targets{$target}->[0];
      my $c = $targets{$target}->[1];
      if (not @$c) {
         print " has no cmd\n";
      }else {
         print " has cmd: ";
         foreach my $cm (@$c){
            print "$cm, \n";
         }
      }
      print "\n";
   }
   print "\n";
}

my $total = $#ARGV + 1;
our $a;

# target is specified #################################################
if ($total > 0){
   foreach $a (@ARGV) {
      evaluate_target();
   }
}

# target not specified ################################################
else {
   #build first target in Makefile
   my $deps = $targets{$first[0]}->[0];
   my $cmd = $targets{$first[0]}->[1];
   
   if ($cmd){
      $a = $first[0];
      evaluate_target();
   }
   else{
      foreach my $d (@$deps){
         $a = $d;
         evaluate_target();
      }
   }
}

# evaluate targets and execute commands ###############################
sub evaluate_target {   
   if (not $a) { return; }
   my $deps = $targets{$a}->[0];
   my $cmd = $targets{$a}->[1];
   my $tartime = mtime $a;

   print "curr target: $a\n";
   if (not $cmd){ # target $a does not have a command
      
      #print "no cmd\n";
      if ($a =~ /./ && $deps){ # if target is not in targets and has a period
         #print "special case\n";
         my @new_sp = split(/\./, $a);
         my $new_t = '%.' . $new_sp[1];
         my $old_d = $targets{$new_t}->[0];
         my $new_d = '';
         $cmd = $targets{$new_t}->[1];
         
         if ($cmd =~ m/($<)*/){ #have to use foreach here
            foreach my $d (@$deps){
               @new_sp = split(/\./, $d);
               $new_d = '%.' . $new_sp[1];
               if ($new_d eq @$old_d[0]){
                  $new_d = $d;
                  last;
               }
            }
            $cmd =~ s/\$</$new_d/g;
            execute $cmd;
         } 
      }
      elsif (not $targets{$a}->[0] && not $targets{$a}->[1]){
         if ($a =~ /./){
            my @new_sp = split(/\./, $a);
            my $new_t = '%.' . $new_sp[1];
            my $new_d = $new_sp[0] . '.java';
            $cmd = $targets{$new_t}->[1];
            foreach my $cm (@$cmd){
               $cm =~ s/\$</$new_d/g;
               execute $cm;
            }
         }
      }

      else {
         foreach my $d (@$deps){
            $a = $d;
            evaluate_target(); # recursively evaluate target
         }
      }
   }

   else { # target $a has a command
      my @arr = handle_macros $a;
      my $m = pop @arr;
      print "target: $m\n";
      $tartime = mtime $m;
      $a = $m;
      
      if (not $tartime){ # $a is not a file, we dont care about time

         #print "not a file\n";
         foreach my $d (@$deps){ # for every dependency
            my @arr = handle_macros ($d);
            
            my $size = @arr;
   
            while ($size > 0) {
               $a = pop @arr;
               $size = @arr;
               evaluate_target(); # recursively evaluate hashref target
            }

         }
         execute $cmd; # execute cmd of $a after all dependencies
      }

      else { # $a is a file, check times
         #print "is a file\n";
         my $time;
         my $currTime = $tartime;
         my $dated = 0;
         foreach my $d (@$deps){ # for each dep, hashref
            my @arr = handle_macros ($d);
            foreach my $val (@arr){
               $time = mtime $val;

               if (not $time){ # we need to create dependency
                  $dated++;
                  $a = $val;
                  evaluate_target();
               }

               elsif ($time > $currTime){ 
                  $dated++; 
               }
            }
         }

         if ($dated > 0){ # dependencies are out of date
            execute $cmd; # execute command of $a
         }
      }
   }
}









