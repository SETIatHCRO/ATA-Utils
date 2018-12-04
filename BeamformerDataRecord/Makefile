CC          = gcc
B2D_LIB_CCFLAGS     = -g -O3 -fPIC -shared -lstdc++ -mavx -msse4 \
                     -I. -I$(CUDA_DIR)/include -I/usr/local/include \
                     -L. -L/usr/local/lib \
                     -lhashpipe -lrt -lm -lpthread
BEAM_READ_TARGET  = beam_read.so
BEAM_WRITE_TARGET = beam_write.so
BEAM_SPLIT_TARGET = beam_split.so
BEAM_CHUNKS_TARGET = beam_chunks.so
B2D_LIB_TARGET   = beam_read.so beam_write.so beam_split.so
BEAM_READ_SOURCE  = beam_read.c
BEAM_WRITE_SOURCE = beam_write.c
BEAM_SPLIT_SOURCE = beam_split.c
BEAM_CHUNKS_SOURCE = beam_chunks.c
B2D_LIB_SOURCES  = beam_read.c beam_write.c beam_split.c beam_chunks.c
B2D_LIB_INCLUDES = beam_databuf.h

all: $(B2D_LIB_TARGET)

$(B2D_LIB_TARGET): $(B2D_LIB_SOURCES) $(B2D_LIB_INCLUDES)
	$(CC) -o $(BEAM_READ_TARGET) $(BEAM_READ_SOURCE) $(B2D_LIB_CCFLAGS)
	$(CC) -o $(BEAM_WRITE_TARGET) $(BEAM_WRITE_SOURCE) $(B2D_LIB_CCFLAGS)
	$(CC) -o $(BEAM_SPLIT_TARGET) $(BEAM_SPLIT_SOURCE) $(B2D_LIB_CCFLAGS)
	$(CC) -o $(BEAM_CHUNKS_TARGET) $(BEAM_CHUNKS_SOURCE) $(B2D_LIB_CCFLAGS)

tags:
	ctags -R .

clean:
	rm -f $(B2D_LIB_TARGET) tags

prefix=/usr/local
LIBDIR=$(prefix)/lib
BINDIR=$(prefix)/bin
install-lib: $(B2D_LIB_TARGET)
	mkdir -p "$(DESTDIR)$(LIBDIR)"
	install -p $^ "$(DESTDIR)$(LIBDIR)"
install: install-lib

.PHONY: all tags clean install install-lib
