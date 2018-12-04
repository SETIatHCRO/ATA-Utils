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
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <linux/limits.h>
#include "hashpipe.h"
#include "beam_databuf.h"

hashpipe_databuf_t *databuf;
static int keep_running = 1;
static char output_dir[1024];
static char filename_prefix[1024];
static int output_port = 0;

#define FILESIZE 136314880
#define SEGMENTS_PER_FILE (FILESIZE/DBUF_BLOCK_SIZE) //8

static int setupSendSocket()
{
        int sendSd = socket(AF_INET, SOCK_DGRAM, 0);
        int optval = 1;
        int ttl = 1;
        setsockopt(sendSd, SOL_SOCKET, SO_REUSEADDR, (char *) &optval, sizeof(optval));
        setsockopt(sendSd, SOL_SOCKET, SO_BROADCAST, (char *) &optval, sizeof(optval));
        setsockopt(sendSd, SOL_SOCKET, IP_TTL, (char *) &ttl, sizeof(ttl));
        if (sendSd < 0) {
                perror("opening datagram socket");
                exit(1);
        }
        return sendSd;

}


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

        hgets(st.buf, "output_dir", 1023, output_dir);
        hgets(st.buf, "filename_prefix", 1023, filename_prefix);
        hgeti4(st.buf, "output_port", &output_port);
        fprintf(stderr, "beam_chunks: output_dir=%s, prefix=%s, port=%d\n", 
            output_dir, filename_prefix, output_port);

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
        int send_socket = 0;
        struct sockaddr_in send1;
        char filename[PATH_MAX];
        int chunk_num = 0;
        int segment_num = 0;
        int i = 0;

        send_socket = setupSendSocket();
        if(send_socket < 0) {
          perror("send_socket error: ");
          fprintf(stderr, "error - can't create send socket\n");
          exit(1);
        }

        memset((char *) &send1, 0, sizeof(send1));
        send1.sin_family = AF_INET;
        send1.sin_addr.s_addr = inet_addr("127.0.0.1");
        send1.sin_port = htons(output_port);


        if(posix_memalign(&buffer, 512, DBUF_BLOCK_SIZE))
        {
          fprintf(stderr, "error - memalign problem %d\n" , errno);
          exit(1);
        }

	sprintf(filename, "%s/%s_%05d.raw\n", output_dir, filename_prefix, chunk_num);
        fout = open(filename, O_CREAT|O_TRUNC|O_WRONLY|O_DIRECT, S_IRWXU);

        //SEGMENTS_PER_FILE

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
          segment_num++;
          if(segment_num == SEGMENTS_PER_FILE) {
            close(fout);
            chunk_num++;
            segment_num = 0;
	    sprintf(filename, "%s/%s_%05d.raw\n", output_dir, filename_prefix, chunk_num);
            fout = open(filename, O_CREAT|O_TRUNC|O_WRONLY|O_DIRECT, S_IRWXU);
          }

          for(i = 0; i<DBUF_BLOCK_SIZE; i+=PACKET_SIZE) {
            n = sendto(send_socket, buffer+i, PACKET_SIZE, 0,
              (struct sockaddr*)&send1, sizeof(send1));
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
