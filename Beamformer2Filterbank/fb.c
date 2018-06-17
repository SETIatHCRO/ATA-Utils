

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "fb.h"

void fbInitHeaderInfo(filterbank_info *info) {

    memset(info, 0, sizeof(filterbank_info));

    info->machine_id = -1;
    info->az_start = 0.0;
    info->za_start = 0.0;
    info->nbeams = 1;
    info->ibeam = 1;

}

FILE *fbOpen(char *filename, filterbank_info *info) {

    if(info->nifs != 1) {
        fprintf(stderr, "Sorry, this program only supports nifs == 1\n");
        return NULL;
    }

    FILE *outputFp = fopen(filename, "wb");

    if(outputFp == NULL) {
        fprintf(stderr, "ERROR opening output file %s.\n", filename);
        return NULL;
    }

    write_string("HEADER_START",outputFp);
    write_string("rawdatafile",outputFp);
    write_string(info->rawdatafile,outputFp);
    if (info->source_name[0] != 0) {
        write_string("source_name",outputFp);
        write_string(info->source_name,outputFp);
    }
    write_int("machine_id",info->machine_id,outputFp);
    write_int("telescope_id",info->telescope_id,outputFp);
    write_coords(info, outputFp);
    /* filterbank data */
    /* N.B. for dedisperse to work, foff<0 so flip if necessary */
    write_int("data_type",1,outputFp);
    write_double("fch1",info->fch1,outputFp);
    write_double("foff",info->foff,outputFp);
    write_int("nchans",info->nchans,outputFp);
    /* beam info */
    write_int("nbeams",info->nbeams,outputFp);
    write_int("ibeam",info->ibeam,outputFp);
    /* number of bits per sample */
    write_int("nbits",info->nbits,outputFp);
    /* start time and sample interval */
    write_double("tstart",info->tstart,outputFp);
    write_double("tsamp",info->tsamp,outputFp);
    write_int("nifs", 1, outputFp);
    write_string("HEADER_END", outputFp);

    return outputFp;
}

void fbClose(FILE *outputFp) {
    if(outputFp == NULL) return;
    fclose(outputFp);
}

int fbWriteFloatData(float *data, int length, FILE *outputFp) {
    if(outputFp == NULL) return 0;
    fwrite(data, sizeof(float), length, outputFp);
    return 1;
}

void write_string(char *string, FILE *outputFp) {
    if(outputFp == NULL) return;
    int len;
    len=strlen(string);
    fwrite(&len, sizeof(int), 1, outputFp);
    fwrite(string, sizeof(char), len, outputFp);
}

void write_float(char *name,float floating_point, FILE *outputFp) {
    if(outputFp == NULL) return;
    write_string(name, outputFp);
    fwrite(&floating_point,sizeof(float),1, outputFp);
}

void write_double (char *name, double double_precision, FILE *outputFp) {
    if(outputFp == NULL) return;
    write_string(name, outputFp);
    fwrite(&double_precision,sizeof(double),1, outputFp);
}

void write_int(char *name, int integer, FILE *outputFp) {
    if(outputFp == NULL) return;
    write_string(name, outputFp);
    fwrite(&integer,sizeof(int),1,outputFp);
}

void write_char(char *name, char integer, FILE *outputFp) {
    if(outputFp == NULL) return;
    write_string(name, outputFp);
    fwrite(&integer,sizeof(char),1,outputFp);
}


void write_long(char *name, long integer, FILE *outputFp) {
    write_string(name, outputFp);
    fwrite(&integer,sizeof(long),1,outputFp);
}

void write_coords(filterbank_info *header_info, FILE *outputFp)
{
    float raj = float2FbRaDecFloat(header_info->src_ra);
    float dej = float2FbRaDecFloat(header_info->src_dec);
    float az = float2FbRaDecFloat(header_info->az_start);
    float za = float2FbRaDecFloat(header_info->za_start);

    if ((raj != 0.0) || (raj != -1.0)) write_double("src_raj",raj, outputFp);
    if ((dej != 0.0) || (dej != -1.0)) write_double("src_dej",dej, outputFp);
    if ((az != 0.0)  || (az != -1.0))  write_double("az_start",az, outputFp);
    if ((za != 0.0)  || (za != -1.0))  write_double("za_start",za, outputFp);
}

/* Convert a float representing an RA or a Dec into the format 
 * necessary for the filterbank header. From page 3 of sigproc.pdf:
 *
 * src raj (double): right ascension (J2000) of source (hhmmss.s)
 * src dej (double): declination (J2000) of source (ddmmss.s)
 */
float float2FbRaDecFloat(float num) {

    int isNeg = 0;
    if(num < 0) {
        isNeg = 1;
        num = fabs(num);
    }

    int d = (int)num;
    int m = (int)((num - d)*60.0);
    float s = ((float)(num - d) - (float)m/60.0)*3600.0;

    float fbVal = d * 10000 + m*100 + s;
    if(isNeg) fbVal = -fbVal;

    return fbVal;

}

void fbPrintHeader(filterbank_info *info) {
    fprintf(stderr,"telescope_id = %d\n", info->telescope_id); //ATA == 9
    fprintf(stderr,"machine_id   = %d\n", info->machine_id);
    fprintf(stderr,"rawdatafile  = %s\n", info->rawdatafile);
    fprintf(stderr,"source_name  = %s\n", info->source_name);
    fprintf(stderr,"tstart       = %lf\n", info->tstart);
    fprintf(stderr,"tsamp        = %lf\n", info->tsamp);
    fprintf(stderr,"fch1         = %lf\n", info->fch1);
    fprintf(stderr,"src_ra       = %lf hours, %02f\n", info->src_ra, float2FbRaDecFloat(info->src_ra));
    fprintf(stderr,"src_dec      = %lf deg, %02f\n", info->src_dec, float2FbRaDecFloat(info->src_dec));
    fprintf(stderr,"az_start     = %lf deg, %02f\n", info->az_start, float2FbRaDecFloat(info->az_start));
    fprintf(stderr,"za_start     = %lf deg, %02f\n", info->za_start, float2FbRaDecFloat(info->za_start));
    fprintf(stderr,"foff         = %lf\n", info->foff);
    fprintf(stderr,"nbits        = %d\n", info->nbits);
    fprintf(stderr,"nchans       = %d\n", info->nchans);
    fprintf(stderr,"nifs         = %d\n", info->nifs);
    fprintf(stderr,"nbeams       = %d\n", info->nbeams);
    fprintf(stderr,"ibeam        = %d\n", info->ibeam);
}

