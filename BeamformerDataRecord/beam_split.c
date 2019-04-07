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
#include "hashpipe.h"
#include "beam_databuf.h"

hashpipe_databuf_t *databuf;
static int keep_running = 1;
static char ip1[512];
static int port1 = 0;
static char ip2[512];
static int port2 = 0;
static int ip2_decimate = 2;

#define FILENAME "/data1/beam.bin"

static int openUDPSocket(char ip_address[16], unsigned short port)
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
        /*
        memset((char *) &localSock, 0, sizeof(localSock));
        localSock.sin_family = AF_INET;
        localSock.sin_port = htons(port);
        //localSock.sin_addr.s_addr  = INADDR_ANY;
        localSock.sin_addr.s_addr  = inet_addr(ip_address);

        if (bind(recvSocket, (struct sockaddr*)&localSock, sizeof(localSock))) {
                perror("binding datagram socket");
                fprintf(stderr, "IP=%s, port=%d\n", ip_address, (int)port);
                close(recvSocket);
                exit(1);
        }
        */


        return recvSocket;
}

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
        printf("BEAM SPLIT Initialization...\n");

        struct sigaction sigIntHandler;
        sigIntHandler.sa_handler = ctrlchandler;
        sigemptyset(&sigIntHandler.sa_mask);
        sigIntHandler.sa_flags = 0;
        sigaction(SIGINT, &sigIntHandler, NULL);

fprintf(stderr, "DBUF_HEADER_SIZE=%d\n", DBUF_HEADER_SIZE);
fprintf(stderr, "DBUF_BLOCK_SIZE=%d\n", DBUF_BLOCK_SIZE);
fprintf(stderr, "DBUF_NUM_BLOCKS=%d\n", DBUF_NUM_BLOCKS);

        hashpipe_status_t st = args->st;

        hgets(st.buf, "ip1", 15, ip1);
        hgeti4(st.buf, "port1", &port1);
        fprintf(stderr, "ip1 = %s, port1=%d\n", ip1, port1);
        hgets(st.buf, "ip2", 15, ip2);
        hgeti4(st.buf, "port2", &port2);
        hgeti4(st.buf, "ip2_decimate", &ip2_decimate);
        fprintf(stderr, "ip2 = %s, port2=%d, decimate=%d\n", ip2, port2, ip2_decimate);
        databuf = hashpipe_databuf_create(MY_INSTANCE, DBUF_ID, DBUF_HEADER_SIZE,
                    DBUF_BLOCK_SIZE, DBUF_NUM_BLOCKS);

        if(databuf == NULL) exit(1);
        return 0;
}

static void *run(hashpipe_thread_args_t * args)
{
        fprintf(stderr, "BEAM SPLIT Running...\n");

        int block_num = 0;
        void *buffer = NULL;
        unsigned char *d;
        int send_socket = 0;
        struct sockaddr_in send1;
        struct sockaddr_in send2;
        int n = 0;
        int count = 0;
        int i = 0;

        send_socket = setupSendSocket();
        if(send_socket < 0) {
          perror("send_socket error: ");
          fprintf(stderr, "error - can't create send socket\n");
          exit(1);
        }
        memset((char *) &send1, 0, sizeof(send1));
        send1.sin_family = AF_INET;
        send1.sin_addr.s_addr = inet_addr(ip1);
        send1.sin_port = htons(port1);
        memset((char *) &send2, 0, sizeof(send2));
        send2.sin_family = AF_INET;
        send2.sin_addr.s_addr = inet_addr(ip2);
        send2.sin_port = htons(port2);

        if(posix_memalign(&buffer, 512, DBUF_BLOCK_SIZE))
        {
          fprintf(stderr, "error - memalign problem %d\n" , errno);
          exit(1);
        }

        while(!hashpipe_databuf_busywait_filled(databuf, block_num))
        {
          d = hashpipe_databuf_data(databuf, block_num);
          memcpy(buffer, d, DBUF_BLOCK_SIZE);
          for(i = 0; i<DBUF_BLOCK_SIZE; i+=PACKET_SIZE) {
            //n = write(fd1, buffer, DBUF_BLOCK_SIZE);
            n = sendto(send_socket, buffer+i, PACKET_SIZE, 0,
                        (struct sockaddr*)&send1,
                       sizeof(send1));
            if(n != PACKET_SIZE)
            {
              printf("n=%d, i=%d, \n", n, i/PACKET_SIZE);
              fprintf(stderr, "Beam split send1 error: %d, n=%d, %s\n", errno,n,strerror(errno));
              break;
            }
            if(count % ip2_decimate == 0) {
              //n = write(fd2, buffer, DBUF_BLOCK_SIZE);
              n = sendto(send_socket, buffer+i, PACKET_SIZE, 0,
                          (struct sockaddr*)&send2,
                         sizeof(send2));
              if(n != PACKET_SIZE)
              {
                fprintf(stderr, "Beam split send2 error: %d, n=%d, %s\n", errno,n,strerror(errno));
                continue;
              }
            }
            count++;
          }
          hashpipe_databuf_set_free(databuf, block_num);
          block_num = (block_num + 1) % DBUF_NUM_BLOCKS;
        }

        close(send_socket);

}

static hashpipe_thread_desc_t beam_split_thread = {
    name: "beam_split_thread",
    skey: "BEAM_SPLIT_STAT",
    init: init,
    run:  run,
    ibuf_desc: {NULL},
    obuf_desc: {NULL}
};

static __attribute__((constructor)) void ctor()
{
  register_hashpipe_thread(&beam_split_thread);
}
