CC = gcc
#CFLAGS = -Wall -Werror
RFOBJS = rfswitch.o
ATTENOBJS = atten.o
LIBS = -lusb -lhid
RFEXE = rfswitch
ATTENEXE = atten

all: $(RFEXE) $(ATTENEXE)

rfswitch: $(RFOBJS)
	$(CC) $(CFLAGS) $(RFOBJS) -o $(RFEXE) $(LIBS)
	rm -f *~ *.o

atten: $(ATTENOBJS)
	$(CC) $(CFLAGS) $(ATTENOBJS) -o $(ATTENEXE) $(LIBS)
	rm -f *~ *.o

rfswitch.o: rfswitch.c
	$(CC) $(CFLAGS) -c rfswitch.c

atten.o: atten.c
	$(CC) $(CFLAGS) -c atten.c

install:
	cp ./rfswitch /usr/local/bin

clean:
	rm -f *~ *.o $(RFEXE)
