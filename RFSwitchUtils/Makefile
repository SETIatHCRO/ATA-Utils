CC = gcc
#CFLAGS = -Wall -Werror
RFOBJS = rfswitch.o
ATTENOBJS = atten.o
LIBS = -lusb -lhid -lpthread
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
	cp ./atten /usr/local/bin
	chmod u+s /usr/local/bin/rfswitch
	chmod u+s /usr/local/bin/atten

clean:
	rm -f *~ *.o $(RFEXE)
