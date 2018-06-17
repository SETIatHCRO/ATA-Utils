#ifndef FB_H
#define FB_H_

#include <linux/limits.h> // For PATH_MAX

typedef struct {
     int telescope_id; //ATA == 9
     int machine_id;
     char rawdatafile[PATH_MAX];
     char source_name[64];
     double tstart;
     double tsamp;
     double fch1;
     double src_ra; //degrees, will be formatted when written
     double src_dec; //degrees, will be formatted when written
     double az_start;
     double za_start;
     double foff;
     int nbits;
     int nchans;
     int nifs;
     int nbeams;
     int ibeam;

} filterbank_info;

void fbInitHeaderInfo(filterbank_info *info );
FILE *fbOpen(char *filename, filterbank_info *info);
void fbClose(FILE *outputFp);
int fbWriteFloatData(float *data, int length, FILE *outputFp);

float float2FbRaDecFloat(float num);

void write_string(char *string, FILE *outputFp);
void write_float(char *name,float floating_point, FILE *outputFp);
void write_double (char *name, double double_precision, FILE *outputFp);
void write_int(char *name, int integer, FILE *outputFp);
void write_char(char *name, char integer, FILE *outputFp);
void write_long(char *name, long integer, FILE *outputFp);
void write_coords(filterbank_info *header_info, FILE *outputFp);
void fbPrintHeader(filterbank_info *info);

#endif // FB_H
