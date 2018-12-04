#define _GNU_SOURCE //Needed for DIRECT_IO
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include "hashpipe.h"
#include "beam_databuf.h"

hashpipe_databuf_t *databuf;
static int keep_running = 1;
static char filename[512];

#define FILENAME "/data1/beam.bin"

void ctrlchandler(int s){
           printf("Caught signal %d\n",s);
           keep_running = 0;
           exit(1); 

}

static int init(hashpipe_thread_args_t * args)
{
        printf("BEAM WRITE Initialization...\n");

        struct sigaction sigIntHandler;
        sigIntHandler.sa_handler = ctrlchandler;
        sigemptyset(&sigIntHandler.sa_mask);
        sigIntHandler.sa_flags = 0;
        sigaction(SIGINT, &sigIntHandler, NULL);

fprintf(stderr, "DBUF_HEADER_SIZE=%d\n", DBUF_HEADER_SIZE);
fprintf(stderr, "DBUF_BLOCK_SIZE=%d\n", DBUF_BLOCK_SIZE);
fprintf(stderr, "DBUF_NUM_BLOCKS=%d\n", DBUF_NUM_BLOCKS);

        hashpipe_status_t st = args->st;

        hgets(st.buf, "file", 511, filename);
        fprintf(stderr, "Filename = %s\n", filename);
        databuf = hashpipe_databuf_create(MY_INSTANCE, DBUF_ID, DBUF_HEADER_SIZE,
                    DBUF_BLOCK_SIZE, DBUF_NUM_BLOCKS);

        if(databuf == NULL) exit(1);
        return 0;
}

static void *run(hashpipe_thread_args_t * args)
{
        printf("BEAM WRITE Running...\n");

        int block_num = 0;
        void *buffer = NULL;
        unsigned char *d;
        int fout = -1;;
        int n = 0;

        fout = open(filename, O_CREAT|O_TRUNC|O_WRONLY|O_DIRECT, S_IRWXU);

        if(posix_memalign(&buffer, 512, DBUF_BLOCK_SIZE))
        {
          fprintf(stderr, "error - memalign problem %d\n" , errno);
          exit(1);
        }

        while(!hashpipe_databuf_busywait_filled(databuf, block_num))
        {
          d = hashpipe_databuf_data(databuf, block_num);
          memcpy(buffer, d, DBUF_BLOCK_SIZE);
          n = write(fout, buffer, DBUF_BLOCK_SIZE);
          if(n != DBUF_BLOCK_SIZE)
          {
            fprintf(stderr, "Beam write error: %d, n=%d, %s\n", errno,n,strerror(errno));
            break;
          }
          hashpipe_databuf_set_free(databuf, block_num);
          block_num = (block_num + 1) % DBUF_NUM_BLOCKS;
        }

        close(fout);

}

static hashpipe_thread_desc_t beam_chunks_thread = {
    name: "beam_chunks_thread",
    skey: "BEAM_CHUNKS_STAT",
    init: init,
    run:  run,
    ibuf_desc: {NULL},
    obuf_desc: {NULL}
};

static __attribute__((constructor)) void ctor()
{
  register_hashpipe_thread(&beam_chunks_thread);
}
