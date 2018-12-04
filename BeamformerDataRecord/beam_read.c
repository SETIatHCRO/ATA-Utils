#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

#include <arpa/inet.h>
#include <netinet/in.h>

#include "hashpipe.h"
#include "hashpipe_udp.h"
#include "fitshead.h"
#include "beam_databuf.h"
#include "hashpipe_error.h"

hashpipe_databuf_t *databuf;
static struct hashpipe_udp_params params;

static int openUDPSocket(unsigned short port)
{
        int recvSocket;
        struct sockaddr_in    localSock;

        /*
         * Create a datagram socket on which to receive.
         **/
        recvSocket = socket(AF_INET, SOCK_DGRAM, 0);
        if (recvSocket < 0) {
                perror("opening datagram socket");
                exit(1);
        }

        /*
         * Enable SO_REUSEADDR to allow multiple instances of this
         * application to receive copies of the multicast datagrams.
         **/
        int reuse=1;

        if (setsockopt(recvSocket, SOL_SOCKET, SO_REUSEADDR,
                                (char *)&reuse, sizeof(reuse)) < 0) {
                perror("setting SO_REUSEADDR");
                close(recvSocket);
                exit(1);
        }

        int n = 256*1024*1024;
        if (setsockopt(recvSocket, SOL_SOCKET, SO_RCVBUF, &n, sizeof(n)) == -1)
        {
                fprintf(stderr,"Set socket size error!\n\n");
        }
        n = 0;
        socklen_t optlen = sizeof(n);
        getsockopt(recvSocket, SOL_SOCKET, SO_RCVBUF, &n, &optlen);
        fprintf(stderr, "REVC socket buffer set to %d\n", n);

        /*
         * Bind to the proper port number with the IP address
         * specified as INADDR_ANY.
         **/
        memset((char *) &localSock, 0, sizeof(localSock));
        localSock.sin_family = AF_INET;
        localSock.sin_port = htons(port);
        localSock.sin_addr.s_addr  = INADDR_ANY;

        if (bind(recvSocket, (struct sockaddr*)&localSock, sizeof(localSock))) {
                perror("binding datagram socket");
                close(recvSocket);
                exit(1);
        }


        return recvSocket;
}

static int init(hashpipe_thread_args_t * args)
{
        hashpipe_status_t st = args->st;

        //Get the port
        int port = 0;
        hgeti4(st.buf, "port", &port);

        printf("BEAM READ Initialization...\n");
        databuf = hashpipe_databuf_attach(MY_INSTANCE, DBUF_ID);

        params.sock = openUDPSocket(port);

/*
        hashpipe_status_t st = args->st;
        //strcpy(params.bindhost,"127.0.0.1");
        strcpy(params.bindhost,"0.0.0.0");
        //selecting a port to listen to
        params.port = 50000;
        params.packet_size = PACKET_SIZE;
        int e = hashpipe_udp_init(&params);
        if(e != HASHPIPE_OK)
        {
          fprintf(stderr, "hashpipe_udp_init error %d\n", e);
          exit(1);
        }
*/

        return 0;
}

static void *run(hashpipe_thread_args_t * args)
{
        char *message;
        int n = 0;
        int total = 0;
        int block_num = 0;
        unsigned char *buffer;
unsigned char b[PACKET_SIZE];

printf("SOCK=%d\n", params.sock);

        printf("BEAM READ Running...\n");
        
        buffer = hashpipe_databuf_data(databuf, block_num);

        while(1)
        {
          n = recv(params.sock, buffer + total, PACKET_SIZE, 0);
          if(n != PACKET_SIZE)
          {
//printf("n=%d, %d\n", n, PACKET_SIZE);
            usleep(20000); // 1/50th of a second
            continue;
          }
          else
          {
//            printf("OK n=%d\n", n);
          }

          total += n;

          if(total == DBUF_BLOCK_SIZE)
          {
            hashpipe_databuf_set_filled(databuf, block_num);
            total = 0;
            block_num = (block_num + 1) % DBUF_NUM_BLOCKS;
            buffer = hashpipe_databuf_data(databuf, block_num);
          }

        }
}

static hashpipe_thread_desc_t beam_read_thread = {
    name: "beam_read_thread",
    skey: "BEAM_READ_STAT",
    init: init,
    run:  run,
    ibuf_desc: {NULL},
    obuf_desc: {NULL}
};

static __attribute__((constructor)) void ctor()
{
  register_hashpipe_thread(&beam_read_thread);
}
