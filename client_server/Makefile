# $Id: Makefile,v 1.9 2018-07-26 14:20:10-07 - - $

MKFILE      = Makefile
DEPFILE     = ${MKFILE}.dep
NOINCL      = ci clean spotless
NEEDINCL    = ${filter ${NOINCL}, ${MAKECMDGOALS}}
GMAKE       = ${MAKE} --no-print-directory

GPPOPTS     = -Wall -Wextra -Wold-style-cast -fdiagnostics-color=never
COMPILECPP  = g++ -std=gnu++17 -g -O0 ${GPPOPTS}
MAKEDEPCPP  = g++ -std=gnu++17 -MM ${GPPOPTS}
UTILBIN     = /afs/cats.ucsc.edu/courses/cmps109-wm/bin

MODULES     = logstream protocol sockets
EXECBINS    = cix cixd
ALLMODS     = ${MODULES} ${EXECBINS}
SOURCELIST  = ${foreach MOD, ${ALLMODS}, ${MOD}.h ${MOD}.tcc ${MOD}.cpp}
ALLSOURCE   = ${wildcard ${SOURCELIST}}
CPPLIBS     = ${wildcard ${MODULES:=.cpp}}
OBJLIBS     = ${CPPLIBS:.cpp=.o}
CIXOBJS     = cix.o ${OBJLIBS}
CIXDOBJS    = cixd.o ${OBJLIBS}

all: ${DEPFILE} ${EXECBINS}

cix: ${CIXOBJS}
	${COMPILECPP} -o $@ ${CIXOBJS}

cixd: ${CIXDOBJS}
	${COMPILECPP} -o $@ ${CIXDOBJS}

%.o: %.cpp
	- ${UTILBIN}/checksource $<
	- ${UTILBIN}/cpplint.py.perl $<
	${COMPILECPP} -c $<

ci: ${ALLSOURCE}
	${UTILBIN}/cid + ${ALLSOURCE}
	- ${UTILBIN}/checksource ${ALLSOURCE}

lis: all ${ALLSOURCE} ${DEPFILE}
	- pkill gv
	${UTILBIN}/mkpspdf ${LISTING} ${ALLSOURCE} ${MKFILE} ${DEPFILE}

clean:
	- rm ${LISTING} ${LISTING:.ps=.pdf} ${OBJECTS} core

spotless: clean
	- rm ${EXECBINS} ${DEPFILE}


dep: ${ALLCPPSRC}
	@ echo "# ${DEPFILE} created `LC_TIME=C date`" >${DEPFILE}
	${MAKEDEPCPP} ${ALLSOURCE} >>${DEPFILE}

${DEPFILE}:
	@ touch ${DEPFILE}
	${GMAKE} dep

again: ${ALLSOURCE}
	${GMAKE} spotless dep ci all lis

ifeq (${NEEDINCL}, )
include ${DEPFILE}
endif

