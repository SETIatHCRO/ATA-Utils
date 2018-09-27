/*
 * atten.c
 * Jon Richards - SETI Institute, June 06, 2018
 *
 * This program controls the Mini Circuits attenuateo PN: RUDAT-6000-30
 * This program was modified from an example located at:
 * https://www.minicircuits.com/softwaredownload/Prog_Examples_Troubleshooting.pdf
 * The program has been modified to allow more than one device and print help.
 * Run atten with no arguments to print out help.
 */


// Requires libusb and libhid libraries for USB control available under GNU GPL license
#include <usb.h>
#include <hid.h>
#include <stdio.h>
#include <string.h>
#include "antassign.h"
#define VENDOR_ID 0x20ce // MiniCircuits Vendor ID
#define PRODUCT_ID 0x0023 // MiniCircuits HID USB RUDAT Product ID
#define PATHLEN 2
#define SEND_PACKET_LEN 64
HIDInterface* hid;
hid_return ret;
struct usb_device *usb_dev;
struct usb_dev_handle *usb_handle;
char buffer[80], kdname[80];
const int PATH_IN[PATHLEN] = { 0x00010005, 0x00010033 };
char PACKET[SEND_PACKET_LEN];

static int matcher_try_count = 0;
static int matcher_index = 0;
static bool usb_defined_already = false;

void initDevice();

void cleanup_all(int exit_code, char *message) {
        hid_delete_HIDInterface(&hid);
        hid_cleanup();
	fprintf(stderr,"%s\n", message);
	cleanup(exit_code);
}

void printHelp() {

        fprintf(stderr, "Minicircuits attenuator control.\n\n");
        fprintf(stderr, "atten <comma sep list of db> <comma sep list of ant pols>\n");
        fprintf(stderr, "  attenuation, in dB 0.0 to 31.75\n");
        fprintf(stderr, "    -1 will print out the part number and serial number then exit.\n");
	fprintf(stderr, "   or\n");
        fprintf(stderr, "atten -discover\n");
        fprintf(stderr, "  discover all attenuators on the USB bus\n");
        fprintf(stderr, "Will print OK\\n if successful. Otherwise an error will be reported.\n");
        fprintf(stderr, "**REMEMBER to run as root!!**\n");
	cleanup(0);

}

bool custom_matcher(struct usb_dev_handle const* usbdev,
    void* custom, unsigned int len) {

        struct usb_device const* dev = usb_device((usb_dev_handle*)usbdev);
        //printf("PRODUCT_ID=%X\n", PRODUCT_ID);
        //printf("Matcher... %X, %X\n", dev->descriptor.idVendor, dev->descriptor.idProduct);

        if(dev->descriptor.idVendor == VENDOR_ID && dev->descriptor.idProduct == PRODUCT_ID) {
                if(matcher_try_count++ == matcher_index) {
			//fprintf(stderr,"matcher_try_count=%d\n", matcher_try_count);
                        return true;
                }
        }
        return false;
}


bool match_serial_number(struct usb_dev_handle * usbdev, void* custom, unsigned int len)
{
	bool ret;
	char* buffer = (char*)malloc(len);
	usb_get_string_simple(usbdev, usb_device(usbdev)->descriptor.iSerialNumber,
			buffer, len);
	ret = strncmp(buffer, (char*)custom, len) == 0;
	free(buffer);
	return ret;
}
static struct usb_device *device_init(void)
{
	struct usb_bus *usb_bus;
	struct usb_device *dev;
	usb_init();
	usb_find_busses();
	usb_find_devices();
	for (usb_bus = usb_busses; usb_bus; usb_bus = usb_bus->next)
	{
		for (dev = usb_bus->devices; dev; dev = dev->next)
		{
			if ((dev->descriptor.idVendor == VENDOR_ID) &&
					(dev->descriptor.idProduct == PRODUCT_ID)) {
				return dev;
			}
		}
	}
	return NULL;
}

void Get_PN (char* PNstr)
{
	int i;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=40; // PN code
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,2000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "1hid_interrupt_write failed with return code %d\n", ret);
	}
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	if (ret == HID_RET_SUCCESS) {
		strncpy(PNstr,PACKETreceive,SEND_PACKET_LEN);
		for (i=0;PNstr[i+1]!='\0';i++) {
			PNstr[i]=PNstr[i+1];
		}
		PNstr[i]='\0';
	}
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "2hid_interrupt_read failed with return code %d\n", ret); }
}
void Get_SN (char* SNstr)
{
	int i;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=41; // SN Code
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "3id_interrupt_write failed with return code %d\n", ret);
	}
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	if (ret == HID_RET_SUCCESS) {
		strncpy(SNstr,PACKETreceive,SEND_PACKET_LEN);
		for (i=0;SNstr[i+1]!='\0';i++) {
			SNstr[i]=SNstr[i+1];
		}
		SNstr[i]='\0';
	}
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "4hid_interrupt_read failed with return code %d\n", ret); }
}
void ReadAtt (char* AttStr)
{
	int i;

	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=18; // Ruturn attenuation code
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "5hid_interrupt_write failed with return code %d\n", ret);
	}
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	if (ret == HID_RET_SUCCESS) {
		strncpy(AttStr,PACKETreceive,SEND_PACKET_LEN);
		for (i=0;AttStr[i+1]!='\0';i++) {
			AttStr[i]=AttStr[i+1];
		}
		AttStr[i]='\0';
	}

	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "6hid_interrupt_read failed with return code %d\n", ret); }
}

void Set_Attenuation (float db)
{
	int i;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=19; // Set Attenuation code is 19.
	PACKET[1]= (int)db;
	float t1=(float)db;
	PACKET[2]= (int) ((t1-PACKET[1])*4);
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "7hid_interrupt_write failed with return code %d\n", ret);
	}
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	// Read packet Packetreceive[0]=1
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "4hid_interrupt_read failed with return code %d\n", ret); }
}

IndexAndPort **getMatcherIndexes(char **antPols, int numAntPols, int *numIndexes) {

        int nextInsertPos = 0;

        //DeviceHookups *deviceHookups = getDeviceHookups(ant, true);
	//DeviceHookups *deviceHookups = getDeviceHookupsFromAntpolList(antPols, numAntPols, true);
	DeviceHookups *deviceHookups = getDeviceHookupsFromAntpolList(antPols, numAntPols, true);
        if(deviceHookups == NULL) return NULL;
        if(deviceHookups->numValid == 0) return NULL;

        IndexAndPort **indexAndPort = (IndexAndPort **)calloc(deviceHookups->num, sizeof(IndexAndPort *));
        for(int i = 0; i<deviceHookups->num; i++) {
                indexAndPort[i] = (IndexAndPort *)calloc(1, sizeof(IndexAndPort));
                indexAndPort[i]->matcherIndex = -4;
                indexAndPort[i]->switchPortNum = -4;
        }
        *numIndexes = deviceHookups->num;

        int matcherIndex = 0;
        initDevice();
        HIDInterfaceMatcher matcher = { VENDOR_ID, PRODUCT_ID, custom_matcher, NULL, 0 };
        ret = hid_init();
        if (ret != HID_RET_SUCCESS) {
                fprintf(stdout, "hid_init failed with return code %d\n", ret);
                return NULL;
        }
        hid = hid_new_HIDInterface();
        if (hid == 0) {
                fprintf(stdout, "hid_new_hidinterface() failed, out of memory?\n");
                return NULL;
        }

        while(1) {

                matcher_try_count = 0;
                ret = hid_force_open(hid, 0, &matcher, 3);
                if (ret != HID_RET_SUCCESS) {
                        //This signifies we ran out of devices
                        //fprintf(stdout, "hid_force_open failed with return code %d\n", ret);
                        //return matchIndexes;
                }

                char PNreceive[SEND_PACKET_LEN];
                char SNreceive[SEND_PACKET_LEN];
                Get_PN(PNreceive);
                //fprintf(stdout," PN= %s .\n",PNreceive);
                Get_SN(SNreceive);
                //fprintf(stdout," SN= %s .\n",SNreceive);

                for(int i = 0; i<deviceHookups->num; i++) {


                        if(!strcmp(SNreceive, deviceHookups->deviceHookups[i]->atten_sn)) {
                                indexAndPort[nextInsertPos]->matcherIndex = matcher_index;
                                indexAndPort[nextInsertPos]->switchPortNum = deviceHookups->deviceHookups[i]->portNum;
                                strcpy(indexAndPort[nextInsertPos]->pn, PNreceive);
                                strcpy(indexAndPort[nextInsertPos]->sn, SNreceive);
                                strcpy(indexAndPort[nextInsertPos]->antPol, deviceHookups->deviceHookups[i]->antPol);
				indexAndPort[nextInsertPos]->origListIndex = deviceHookups->deviceHookups[i]->origListIndex;
                                nextInsertPos++;
                                //printf("Match pos = %d\n",  matcher_index);
                                if(deviceHookups->num == nextInsertPos) {
                                        hid_close(hid);
                                        return indexAndPort;
                                }
                        }

                }
                matcher_index++;

                hid_close(hid);
        }

        return NULL;

}

void initDevice() {
	if(usb_defined_already == true) return;
//	if(usb_defined_already == false) return;
        usb_dev = device_init();
        if (usb_dev == NULL)
        {
                fprintf(stdout, "USB, cannot init!\n");
		cleanup_all(-1, "");
        }
        usb_handle = usb_open(usb_dev);
        int drstatus = usb_get_driver_np(usb_handle, 0, kdname, sizeof(kdname));
        if (kdname != NULL && strlen(kdname) > 0) {
                usb_detach_kernel_driver_np(usb_handle, 0);
        }

        usb_reset(usb_handle);
        usb_close(usb_handle);
        usb_defined_already = true;
}


void discoverPorts() {

        int matcherIndex = 0;
        initDevice();
        HIDInterfaceMatcher matcher = { VENDOR_ID, PRODUCT_ID, custom_matcher, NULL, 0 };
        ret = hid_init();
        if (ret != HID_RET_SUCCESS) {
                fprintf(stdout, "hid_init failed with return code %d\n", ret);
                return;
        }
        hid = hid_new_HIDInterface();
        if (hid == 0) {
                fprintf(stdout, "hid_new_hidinterface() failed, out of memory?\n");
                return;
        }

        while(1) {

                matcher_try_count = 0;
                ret = hid_force_open(hid, 0, &matcher, 1);
                if (ret != HID_RET_SUCCESS) {
                        fprintf(stderr, "hid_force_open failed with return code %d\n", ret);
                        return;
                }

                char PNreceive[SEND_PACKET_LEN];
                char SNreceive[SEND_PACKET_LEN];
                Get_PN(PNreceive);
                fprintf(stdout," PN= %s .\n",PNreceive);
                Get_SN(SNreceive);
                fprintf(stdout," SN= %s .\n",SNreceive);
                matcher_index++;

                hid_close(hid);
        }

}

int main( int argc, unsigned char **argv)
{

	lock();

	//hid_set_debug(HID_DEBUG_ALL);
	//hid_set_usb_debug(HID_DEBUG_ALL);
	if(argc > 1 && !strncmp(argv[1], "-d", 2)) {
		discoverPorts();
		cleanup_all(0, "");
	}
	if(argc != 3) printHelp(); //will exit


	int numAntPols = 0;
	char **antPolList = commaSepListStringToStringArray(argv[2], &numAntPols, true);
	int numAntPolsDB = 0;
	char **antDBList = commaSepListStringToStringArray(argv[1], &numAntPolsDB, false);

	if(numAntPols != numAntPolsDB) {
		fprintf(stderr, "ERROR: Num ant pols [%d] not equal number of dB values [%d]\n",
			numAntPols, numAntPolsDB);
		printHelp();
	}


	//printArrayValues("Ant pols", antPolList, numAntPols);
	//printArrayValues("dB values", antDBList, numAntPolsDB);


	int numIndexes = -1;
	IndexAndPort **matcherIndexes = getMatcherIndexes(antPolList, numAntPols, &numIndexes);
	//fprintf(stdout, "Num indexes = %d\n", numIndexes);
	if(matcherIndexes == NULL) {
		fprintf(stdout, "no attenuator for %s\n", argv[2]);
		cleanup_all(1, "OK");
	}

	//printf("NUM=%d\n", numIndexes);
	for(int i = 0; i<numIndexes; i++) {

 		matcher_try_count = 0;
                matcher_index = matcherIndexes[i]->matcherIndex;

		char AttValue[3];
		float LastAtt=0.0;

		initDevice();

		HIDInterfaceMatcher matcher = { VENDOR_ID, PRODUCT_ID, custom_matcher, NULL, 0 };

		ret = hid_force_open(hid, 0, &matcher, 3);
		if(!hid) {
			fprintf(stderr, "Unable to open device\n");
        		cleanup_all(1, "");
		}
		char PNreceive[SEND_PACKET_LEN];
		char SNreceive[SEND_PACKET_LEN];
		int StrLen1;
		Get_PN(PNreceive);
		//fprintf(stderr," PN= %s .\n",PNreceive);
		Get_SN(SNreceive);
		//fprintf(stderr," SN= %s .\n",SNreceive);
		Set_Attenuation(atof(antDBList[matcherIndexes[i]->origListIndex])); // set attenuation
		ReadAtt ( AttValue);
		LastAtt=(int)(AttValue[0])+(float)(AttValue[1])/4;

 		printf("{ \"antpol\" : \"%s\", \"sn\" : \"%s\", \"pn\" : \"%s\", \"atten_db\" : %f }\n",
                        matcherIndexes[i]->antPol,
                        matcherIndexes[i]->sn, matcherIndexes[i]->pn, LastAtt );

		ret = hid_close(hid);
		if (ret != HID_RET_SUCCESS) {
			fprintf(stderr, "hid_close failed with return code %d, atten read was %f db\n", ret, LastAtt);
        		cleanup_all(1, "");
		}

	}

	cleanup_all(0, "OK");
}
