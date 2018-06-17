CC = gcc
CFLAGS = -Wall -Werror
OBJS = bf2fb.o fb.o
LIBS = -lfftw3f -lm
EXE = bf2fb

all: $(EXE)

bf2fb: $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(EXE) $(LIBS)
	rm -f *~ *.o

bf2fb.o: bf2fb.c
	$(CC) $(CFLAGS) -c bf2fb.c

fb.o: fb.c
	$(CC) $(CFLAGS) -c fb.c

install:
	cp ./bf2fb /usr/local/bin	
clean:
	rm -f *~ *.o $(EXE)
