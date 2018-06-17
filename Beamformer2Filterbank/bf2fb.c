#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/limits.h>
#include <math.h>
//#include <fftw.h>
#include <fftw3.h>
#include "fb.h"

#define IP_ADDRESS_CHAR_SIZE 16 //Including null at end

typedef struct _packetHeader
{
        uint8_t group, version, bitsPerSample, binaryPoint;
        uint32_t order;
        uint8_t type, streams, polCode, hdrLen;
        uint32_t src;
        uint32_t chan;
        uint32_t seq;
        double freq;
        double sampleRate;
        float usableFraction;
        float reserved;
        uint64_t absTime;
        uint32_t flags;
        uint32_t len;
}PacketHeader;

#define DATA_BUF_SIZE 4160
#define DATA_SIZE (DATA_BUF_SIZE - sizeof(PacketHeader))
#define SAMPLES_PER_PACKET 2048

struct sockaddr_in    localSock;
struct ip_mreq        group;
int                   sd;
int                   datalen;
unsigned char         databuf[DATA_BUF_SIZE];

fftwf_complex *fft_in, *fft_out;
fftwf_plan fft_plan;

// Command line arguments
char multicastAddress[IP_ADDRESS_CHAR_SIZE];
unsigned short port = 0;
char filename[PATH_MAX];
char outputFilename[PATH_MAX];
char sourceName[256];
int useFilename = 0;
int useMulticast = 0;
int headerOnly = 0;
float outputCenterFreqMHz = 0.0;
float outputBWHz = 0.0;
int fftSize = 1024;
int intUs = 10000000;
float ra = 0.0;
float dec = 0.0;

typedef struct _timeval 
{
	long tv_sec;//         seconds;
	long tv_usec;//   microseconds;
}timeval;

filterbank_info fbheader;

int ispowerof2(unsigned int x);
void runTests();

void printHelp()
{
	printf("fft - Utility to read beamformer data from a file or socket and produce stats.\n");
	printf("  Syntax:\n");
	printf("    fft <-output filename> <-source sourcename> [-m <multicast address>] [-p <port>] [-input filename] [-outfreq MHz -outbw hz] [-header] [-fftsize <size>] [-int <microseconds>] <-ra RA> <-dec dec>\n");
	printf("      Center frequency of the input data is determined from the beamformer header.\n");
	printf("      if -f specied the data is read from a file and the -m and -p options are ignored.\n");
	printf("      if -f or -m not specified, this program will receive on unicast.\n");
	printf("      -m - the multicast address to receive the data.\n");
	printf("      -p - the ethernet port for read from.\n");
	printf("      -outfreq specifies the center frequency of the output stats. If not specified the\n");
	printf("        center frequency of the incomming data will be used.\n");
	printf("      -outbw int HERTZ, specifies the bandwidth of the output stats. If not specified the\n");
	printf("        entire bandwidth of the incomming data will be used.\n");
	printf("      -header - reads in the first data packet, prints out the header to stdout, then exits.\n");
	printf("      -fftsize - size of the FFT, defaults to 1024.\n");
	printf("      -int - integration time in microseconds. Defaults to 10,000,000 (10 seconds).\n");
	exit(1);
}

timeval absTimeToTimeval(uint64_t absTime)
{
	timeval tv;
	tv.tv_sec = absTime >> 32;
        fprintf(stderr, "SECS=%u\n", (unsigned int)tv.tv_sec);
	double f = (absTime & 0xffffffff) / 4294967296.0;
	tv.tv_usec = (uint32_t) (f * 1e6);
	return (tv);
}

void runTests() {

    fprintf(stderr, "90.000   = %.01f\n", float2FbRaDecFloat(90.000));
    fprintf(stderr, "-90.000  = %.01f\n", float2FbRaDecFloat(-90.000));
    fprintf(stderr, "89.553   = %.01f\n", float2FbRaDecFloat(89.553));
    fprintf(stderr, "-89.553  = %.01f\n", float2FbRaDecFloat(-89.553));
    fprintf(stderr, "179.553  = %.01f\n", float2FbRaDecFloat(179.553));
    fprintf(stderr, "-179.553 = %.01f\n", float2FbRaDecFloat(-179.553));

}

PacketHeader *getHeader(unsigned char *data) {
    return (PacketHeader *)data;
}

unsigned int getSecsFromHeader(unsigned char *data) {
    PacketHeader *header = (PacketHeader *)data;
    unsigned int sec = header->absTime >> 32;
    fprintf(stderr, "SECS=%u\n", sec);
    return (unsigned int)sec;
}

void printTime(unsigned char *db)
{
    PacketHeader header;
    memcpy(&header, db, sizeof(header));
    timeval tv = absTimeToTimeval(header.absTime);
    //fprintf(stdout, "%lX,%s", header.absTime,ctime(&tv.tv_sec));
    fprintf(stdout, "Time:         %s", ctime(&tv.tv_sec));
}

void numToRaOrDec(double num) {
}

double mjd(time_t epoch_time)
{
    return epoch_time / 86400.0 + 40587;
}

//./filterbank_header -o blah -nifs 1 -fch1 1420 -source B0329+54 -filename foobar.bin 
// -telescope ARECIBO -src_raj 032900 -src_dej 540000 -tsamp 65 -foff -0.25 -nbits 8 
// -nchans 1024 -tstart 53543.23
FILE *gatherHeaderdata(PacketHeader *header, int fft_size, char *sourcename, float tstamp) {

    double fullBW = header->sampleRate*1000000.0;
    int numChannels = fft_size;
    double channelWidth = (fullBW / (double)numChannels)/1000000.0;
    fprintf(stderr,"channelWidth = %lf, fullBW=%lf, numChannels=%d\n",
            channelWidth, fullBW, numChannels);
    fprintf(stderr,"header->freq=%lf, header->sampleRate=%lf, channelWidth=%lf\n",
            header->freq, header->sampleRate, channelWidth);
    //double middleFirstChannel = ((header->freq - (header->sampleRate / 2.0)) + channelWidth/2.0);
    double middleFirstChannel = ((header->freq + (header->sampleRate / 2.0)) - channelWidth/2.0);
    unsigned int secs = getSecsFromHeader((unsigned char *)header);
    double time_mjd = mjd((time_t)secs);

    //double tstamp = (double)intUs/1000000.0;

    // Get the source ra/dec
    /*
    char command[256];
    sprintf(command, "ssh atasys@10.3.0.59 atacheck %s", sourcename);
    FILE *fp = popen(command,"r"); 
    // read output from command 
    int n = fscanf(fp,"%s\n", command);   // or other STDIO input functions
    int lineCount = 0;
    double ra = 0.0;
    double dec = 0.0;
    while(n > 0) {
      if(lineCount++ == 6) {
          fprintf(stderr, "%s\n", command);
          sscanf(command, "%lf,%lf\n", &ra, &dec);
          fprintf(stderr,"RA=%lf, DEC=%lf\n", ra, dec);
      }
      n = fscanf(fp,"%s\n", command);   // or other STDIO input functions 
    }
    fclose(fp);
    */

    // ssh atasys@10.3.0.59 atacheck w3oh

    fbInitHeaderInfo(&fbheader);
    strcpy(fbheader.rawdatafile, filename);
    strcpy(fbheader.source_name, sourcename);
    fbheader.nifs      = 1;
    fbheader.nbits     = 32;
    fbheader.fch1      = middleFirstChannel;
    fbheader.telescope_id = 9; //ATA
    fbheader.foff      = -channelWidth;
    fbheader.tsamp     = tstamp;
    fbheader.nchans    = fftSize;
    fbheader.tstart    = time_mjd;
    fbheader.src_ra    = ra;
    fbheader.src_dec   = dec;

    fbPrintHeader(&fbheader);

    fprintf(stderr, "OUTPUT FILENAME = %s\n", outputFilename);

    return fbOpen(outputFilename, &fbheader);
    /*
    //./filterbank_header -o ./test.bin.hdr -nifs 1 -fch1 0.003730 -telescope ATA -foff 800.000000 -tsamp 10.000000
    fprintf(stderr, "./filterbankheader -o %s.hdr -filename %s -source %s -nifs 1 -fch1 %lf -telescope ATA -foff %lf -tsamp %lf -nchans %d -nbits 32 -tstart %lf\n", 
            outputFilename, filename, sourcename,
            middleFirstChannel, channelWidth, tstamp, fftSize, time_mjd);
    */

    //exit(0);

}

void printBFHeader(unsigned char *data)
{
    PacketHeader header;

    memcpy(&header, data, sizeof(header));
    printf("Header len:   %d\n", (int)sizeof(header));
    printf("GROUP:        %d\n", header.group);
    printf("VERSION:      %d\n", header.version);
    printf("BITS/SAMPLE:  %d\n", header.bitsPerSample);
    printf("BINARY_POINT: %d\n", header.binaryPoint);
    printf("ORDER:        %X\n", header.order);
    printf("TYPE:         %d\n", header.type);
    printf("STREAMS:      %d\n", header.streams);
    printf("POL_CODE:     %d\n", header.polCode);
    printf("HDR_LEN:      %d\n", header.hdrLen);
    printf("SRC:          %d\n", header.src);
    printf("CHAN:         %d\n", header.chan);
    printf("SEQ:          %u\n", header.seq);
    printf("SAMPLE_RATE:  %lf\n", header.sampleRate);
    printf("FREQ:         %lf\n", header.freq);
    printf("USE_FRACTION: %f\n", header.usableFraction);
    printTime(data);
    printf("FLAGS:        %u\n", header.flags);
    printf("DATA LEN:     %d\n", (int)header.len);

}

double getSampleRate(unsigned char *data)
{
    PacketHeader header;

    memcpy(&header, data, sizeof(header));
    return header.sampleRate;
}

int getSeq(unsigned char *db)
{
    PacketHeader header;
    memcpy(&header, db, sizeof(header));
    return header.seq;
}

void readArgs(int argc, char *argv[]) {

    int i = 0;

    memset(multicastAddress, 0, sizeof(multicastAddress));
    memset(filename, 0, sizeof(filename));
    memset(outputFilename, 0, sizeof(outputFilename));
    memset(databuf, 0, DATA_BUF_SIZE);

    //Read in the command line args
    if(argc < 2 || !strncmp(argv[1], "-h", 2))
    {
        printHelp(); //exits
    }

    // If the first arg is -test, then run some tests and exit
    if(!strncmp(argv[1], "-test", strlen("-test"))) {
        fprintf(stderr, "Running tests...\n\n");
        runTests();
        exit(0);
    }

    for(i = 1; i<(argc-1); i++) {
        if(!strncmp(argv[i], "-output", strlen("-output"))) {
            memcpy(outputFilename, argv[i+1], strlen(argv[i+1]));
        }
        else if(!strncmp(argv[i], "-source", strlen("-source"))) {
            memcpy(sourceName, argv[i+1], strlen(argv[i+1]));
        }
        else if(!strncmp(argv[i], "-input", strlen("-input"))) {
            memcpy(filename, argv[i+1], strlen(argv[i+1]));
            useFilename = 1;
        }
        else if(!strncmp(argv[i], "-m", strlen("-m"))) {
            memcpy(multicastAddress, argv[i+1], strlen(argv[i+1]));
            if(!useFilename) useMulticast = 1;
        }
        //-outfreq freq -outbw mhz
        else if(!strncmp(argv[i], "-outfreq", strlen("-outfreq"))) {
            outputCenterFreqMHz = atof(argv[i+1]);
        }
        else if(!strncmp(argv[i], "-outbw", strlen("-outbw"))) {
            outputBWHz = atof(argv[i+1]);
        }
        else if(!strncmp(argv[i], "-ra", strlen("-ra"))) {
            ra = atof(argv[i+1]);
        }
        else if(!strncmp(argv[i], "-dec", strlen("-dec"))) {
            dec = atof(argv[i+1]);
        }
        else if(!strncmp(argv[i], "-p", strlen("-p"))) {
            port = (unsigned short)atoi(argv[i+1]);
        }
        else if(!strncmp(argv[i], "-fftsize", strlen("-fftsize"))) {
            fftSize = (int)atoi(argv[i+1]);
            if(!ispowerof2(fftSize)) {
                fprintf(stderr, "Error: -fftsize is %d, not a power of 2\n", fftSize);
                exit(-1);
            }
        }
        else if(!strncmp(argv[i], "-int", strlen("-int"))) {
            intUs = (int)atoi(argv[i+1]);
        }
    }
    for(i = 0; i<argc; i++) {
        if(!strncmp(argv[i], "-header", strlen("-header"))) {
            headerOnly = 1;
        }
    }

}

int openInput() {

    if(useFilename) {
        int fd = open(filename, O_RDONLY);
        if(fd < 0) {
            perror("opening input file");
            exit(1);
        }
        return fd;
    }
    else { //unicast or multicast

        int sd = -1;

        /*
         * Create a datagram socket on which to receive.
         **/
        sd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sd < 0) {
            perror("opening datagram socket");
            exit(1);
        }

        /*
         * Enable SO_REUSEADDR to allow multiple instances of this
         * application to receive copies of the multicast datagrams.
         **/
        {
            int reuse=1;

            if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR,
                        (char *)&reuse, sizeof(reuse)) < 0) {
                perror("setting SO_REUSEADDR");
                close(sd);
                exit(1);
            }
        }

        /*
         * Bind to the proper port number with the IP address
         * specified as INADDR_ANY.
         **/
        memset((char *) &localSock, 0, sizeof(localSock));
        localSock.sin_family = AF_INET;
        localSock.sin_port = htons(port);
        localSock.sin_addr.s_addr  = INADDR_ANY;

        if (bind(sd, (struct sockaddr*)&localSock, sizeof(localSock))) {
            perror("binding datagram socket");
            close(sd);
            exit(1);
        }

        /*
         * Join the multicast group 225.1.1.1 on the local 9.5.1.1
         * interface.  Note that this IP_ADD_MEMBERSHIP option must be
         * called for each local interface over which the multicast
         * datagrams are to be received.
         **/
        if(useMulticast)
        {
            memset(&group, 0, sizeof(group));
            group.imr_multiaddr.s_addr = inet_addr(multicastAddress);
            group.imr_interface.s_addr = htonl(INADDR_ANY);
            //group.imr_interface.s_addr = inet_addr("10.1.51.68");
            if (setsockopt(sd, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                        (char *)&group, sizeof(group)) < 0) {
                perror("adding multicast group");
                close(sd);
                exit(1);
            }
            printf("Multicast\n");
        }
        else {
            printf("Unicast\n");
        }

        return sd;
    }

}

int checkArgs() {

    fprintf(stderr,"\n");

    if(outputFilename[0] == 0) {
        fprintf(stderr, "Error: must specify an output file with the -output <filename> argument.\n\n");
        printHelp();
    }

    if(sourceName[0] == 0) {
        fprintf(stderr, "Error: must specify sourceName with the -source <source name> argument.\n\n");
        printHelp();
    }

    if(useFilename) {
        fprintf(stderr, "Input: File named %s\n", filename);
    }

    if(useMulticast) {
        fprintf(stderr, "Input: multicast address %s, port %d\n",
                multicastAddress, (int)port);
        fprintf(stderr, "Input: multicast port %d\n", (int)port);
    }
    else if(!useFilename) {
        fprintf(stderr, "Input: unicast port %d\n", (int)port);
    }
    if(outputCenterFreqMHz == 0.0) {
        fprintf(stderr, "Stats center will be read from header.\n");
    }
    else fprintf(stderr, "Stats center %f MHz.\n", outputCenterFreqMHz);
    if(outputBWHz == 0.0) {
        fprintf(stderr, "Stats bandwidth will be read from header.\n");
    }
    else fprintf(stderr, "Stats bandwidth %f MHz.\n", outputBWHz);

    fprintf(stderr, "FFT size: %d\n", fftSize);
    fprintf(stderr, "Integration time: %d microseconds\n", intUs);

    if(headerOnly) fprintf(stderr, "Printing first data header, then exiting.\n");

    fprintf(stderr,"\n\n");

    return 1;

}

int ispowerof2(unsigned int x) {
    return x && !(x & (x - 1));
}

void fftInit() {

    fft_in = (fftwf_complex*) fftwf_malloc(sizeof(fftw_complex) * fftSize);
    fft_out = (fftwf_complex*) fftwf_malloc(sizeof(fftw_complex) * fftSize);
    //fft_plan = fftwf_plan_dft_1d(fftSize,fft_in, fft_out, FFTW_FORWARD, FFTW_ESTIMATE);
    fft_plan = fftwf_plan_dft_1d(fftSize,fft_in, fft_out, FFTW_FORWARD, FFTW_MEASURE);
}

void fftDestroy() {

    fftwf_destroy_plan(fft_plan);
    fftwf_free(fft_in);
    fftwf_free(fft_out);
}

// Dump out the power values
void dump(float *power, int len, FILE *outputFp) {

    /*
    int i = 0;
    float max = 0;
    int max_i = -1;
    for(i = 0; i<len; i++) {
        //printf("[%d]%f,", i, power[i]);
	if(power[i] > max) {
		max = power[i];
		max_i = i;
	}
    }
    */

    //fbWriteFloatData(power, len, outputFp);
    // Swap positive, negative
    //power[0] = power[1];
    //fbWriteFloatData(power, len, outputFp);

	/*
    int i = len - 1;
    int j = 0;
    float temp = 0.0;
    while(i > j)
    {
	    temp = power[i];
	    power[i] = power[j];
	    power[j] = temp;
	    i--;
	    j++;
    }
    */

    fbWriteFloatData(power + len/2, len/2, outputFp);
    fbWriteFloatData(power, len/2, outputFp);
    //int success = fbWriteFloatData(power, len, outputFp);
    //fprintf(stderr, "Dump success = %d\n", success);
    /*
    i = 0;
    for(i = 0; i<len; i++) {
        printf("[%d]%f,", i, power[i]);
    }
    */

}

int main (int argc, char *argv[])
{
	int i = 0;
	int j = 0;
	int k = 0;

	memset(multicastAddress, 0, sizeof(multicastAddress));
	memset(filename, 0, sizeof(filename));
	memset(outputFilename, 0, sizeof(outputFilename));
	memset(sourceName, 0, sizeof(sourceName));
	memset(databuf, 0, DATA_BUF_SIZE);

	readArgs(argc, argv);

	int inFd = openInput();

	if(inFd < 0) {
		fprintf(stderr, "Problem opening input, exiting...\n\n");
		exit(-1);
	}

	checkArgs();

	int n = 0;
	int packetCount = 0;
	unsigned char *data = NULL;
	float *power = (float *)calloc(fftSize, sizeof(float));
	double sampleRate = 0.0;
	int packetsPerDump = 0;
	int fftCount = 0;

	//position 
	int fft_pos = 0;

	fftInit();

	int firstHeader = 1;

	FILE *outputFp = NULL;

	while(1)
	{
		n = read(inFd, databuf, DATA_BUF_SIZE);

		if (n <= 0) 
		{
			perror("reading datagram message");
			close(sd);
			fftDestroy();
			fbClose(outputFp);
			exit(1);
		}
		else
		{
			data = databuf + sizeof(PacketHeader);

			if(headerOnly) {
				printBFHeader(databuf);
				exit(0);
			}

			if(firstHeader == 1) {
				firstHeader = 0;
				getSecsFromHeader(databuf);
				printTime(databuf);
				sampleRate = getSampleRate(databuf);
				fprintf(stderr,"Sample rate = %lf\n", sampleRate);
				//Calculate the number of packets for each dump
				// sr(s/sec)*intSecs(sec)/(samples/packet)
				packetsPerDump = (int)((double)(sampleRate*1000000.0)*((double)intUs/1000000.0)/(double)SAMPLES_PER_PACKET);
				fprintf(stderr,"Packets per dump = %d\n", packetsPerDump);

				float tstamp = (1.0/51200.0)*(float)packetsPerDump;
				outputFp = gatherHeaderdata((PacketHeader *)databuf, fftSize, sourceName, tstamp );
			}

			packetCount++;
			//fprintf(stderr,"%d,", fftCount);

			// Gather data for an FFT
			i = 0;
			while(i < DATA_SIZE) {
				//fprintf(stderr, "Loop %d\n", i);
				for(j = fft_pos; (j < fftSize) && i <(DATA_SIZE); j++) {
					fft_in[j][0] = (char)data[i++];
					fft_in[j][1] = (char)data[i++]; //Beamformer data is reverse direction
					fft_pos++;
					//fprintf(stderr, "j = %d, i = %d\n", j, i);
					//fprintf(stderr, "count=%d\n", ++count);

					if(j == (fftSize-1)) {
						fftCount++;
						//fprintf(stderr, "FFT: j = %d, i = %d\n", j, i);
						fftwf_execute(fft_plan);

						for(k = 0; k < fftSize; k++) {
							float re = fft_out[k][0];
							float im = fft_out[k][1];
							//power[k] += sqrt(re*re + im*im);
							power[k] += (re*re + im*im);
							fft_pos = 0;
						}

						if(packetCount >= packetsPerDump) {
							packetCount = 0;

							/*
							   for(k = 0; k < fftSize; k++) {
							   power[k] /= fftCount;
							   }
							   */
							dump(power, fftSize, outputFp);
							memset(power, 0, fftSize * sizeof(float));
							fftCount = 0;
						}

						/*
						   nowSeconds = time(NULL);
						   fprintf(stderr,"%f,%f, %lf\n", power[0], power[1], (double)count/(double)(nowSeconds - startSeconds));
						   */
					}
				}
			}

		}

	}

	fbClose(outputFp);
}
