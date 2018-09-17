/* 
 * rfswitch.c
 * Jon Richards - SETI Institute, June 06, 2018
 * 
 * This program controls the Mini Circuits RF switch PN: USB-1SP8T-63H
 * This program was modified from an example located at:
 * https://www.minicircuits.com/softwaredownload/Prog_Examples_Troubleshooting.pdf
 * The program has been modified to allow more than one device and print help.
 * Run rfswitch with no arguments to print out help.
 */
#include <hid.h>
#include <stdio.h>
#include <string.h>
#include <usb.h>
#include "antassign.h"
#define VENDOR_ID 0x20ce // MiniCircuits Vendor ID
#define PRODUCT_ID 0x0022 // MiniCircuits HID USB Control For RF switch Product ID
#define PATHLEN 2
#define SEND_PACKET_LEN 64
HIDInterface* hid;
hid_return ret;
struct usb_device *usb_dev;
struct usb_dev_handle *usb_handle;
char buffer[80], kdname[80];
const int PATH_IN[PATHLEN] = { 0x00010005, 0x00010033 };
char PACKET[SEND_PACKET_LEN];

#define NUM_DEVICES 2
static const unsigned int serial_numbers[] = { 0x00, 0x00 };

static int matcher_try_count = 0;
static int matcher_index = 0;

bool usb_defined_already = false;

void printHelp() {

	fprintf(stderr, "Minicircuits rf switch controller control.\n\n");
	fprintf(stderr, "rfswitch <comma sep list of ant pols or ants>\n");
	fprintf(stderr, " switches the RF switch to the specified ant (does both pols) or single ant pol.\n");
	fprintf(stderr, " Example: \"rfswitch 2a,2jx\n");
	fprintf(stderr, "or\n");
	fprintf(stderr, "rfswitch -info <ant|antPol>\n");
	fprintf(stderr, " -info <ant|antpol>  will print out the RF switch hookup for an ant or antpol.\n");
	fprintf(stderr, " -info all will print out all hookup info.\n");
	fprintf(stderr, " -d will discover all rf switches.\n");
	fprintf(stderr, "Will print OK\\n if successful. Otherwise an error will be reported.\n");
	fprintf(stderr, "**REMEMBER to run as root!!**\n");
	cleanup(0);

}

bool custom_matcher(struct usb_dev_handle const* usbdev,
		void* custom, unsigned int len) {

	struct usb_device const* dev = usb_device((usb_dev_handle*)usbdev);
	if(dev->descriptor.idVendor == VENDOR_ID && dev->descriptor.idProduct == PRODUCT_ID) {
		//printf("PRODUCT_ID=%X\n", PRODUCT_ID);
		//printf("Matcher... %X, %X\n", dev->descriptor.idVendor, dev->descriptor.idProduct);
		if(matcher_try_count++ == matcher_index) {
			return true;
		}
	}
	return false;
}

bool match_serial_number(struct usb_dev_handle* usbdev, void* custom, unsigned int len)
{
	bool ret;
	char* buffer = (char*)malloc(len);
	usb_get_string_simple(usbdev, usb_device(usbdev)->descriptor.iSerialNumber,
			buffer, len);
	//printf("%s\n", buffer);
	ret = strncmp(buffer, (char*)custom, len) == 0;
	free(buffer);
	return ret;
}

// index is 0 based
static struct usb_device *device_init()
{
	struct usb_bus *usb_bus;
	struct usb_device *dev;
	usb_init();
	usb_find_busses();
	usb_find_devices();
	int count = 0;
	for (usb_bus = usb_busses; usb_bus; usb_bus = usb_bus->next)
	{
		for (dev = usb_bus->devices; dev; dev = dev->next)
		{
			//printf("Count=%d, VENDOR=%8X, PROD=%8X\n", count, dev->descriptor.idVendor, dev->descriptor.idProduct);
			if ((dev->descriptor.idVendor == VENDOR_ID) &&
					(dev->descriptor.idProduct == PRODUCT_ID)) {
				if(count == matcher_index) {
					//printf("FOUND, count == %d\n", count);
					return dev;
				}
				count++;
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
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code %d\n", ret);
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
		fprintf(stderr, "hid_interrupt_read failed with return code %d\n", ret); }

}
void Get_SN (char* SNstr)
{
	int i;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=41; // SN Code
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code %d\n", ret);
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
		fprintf(stderr, "hid_interrupt_read failed with return code %d\n", ret); }

}
void Set_Switch ( unsigned char state, int is16)
{
	int i = 0;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0] = 1;
        if(is16 > 0) sprintf(PACKET+1, ":SP16T:STATE:%d", state);
	else sprintf(PACKET+1, ":SP8T:STATE:%d", state);
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code, sending Set_Switch() %d\n", ret);
	}
	memset(PACKETreceive, 0, sizeof(PACKETreceive));
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	//For debugging...
	//for(i=0;i<16; i++) printf("[%d,%c]", PACKETreceive[i], PACKETreceive[i]);
	//for(i=0;i<16; i++) printf("[%c]", PACKETreceive[i]);
	//printf("\n");
	// Read packet Packetreceive[0]=1
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_read failed with return code reading Set_Switch() %d\n", ret); }
}

int Get_Switch (int is16)
{
	int i = 0;
	char PACKETreceive[SEND_PACKET_LEN];

	PACKET[0] = 1;
        if(is16 > 0) sprintf(PACKET+1, ":SP16T:STATE?");
	else sprintf(PACKET+1, ":SP8T:STATE?");
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code, sending Set_Switch() %d\n", ret);
		return -1;
	}
	memset(PACKETreceive, 0, sizeof(PACKETreceive));
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	//for(i=0;i<16; i++) printf("[%d,%c]", PACKETreceive[i], PACKETreceive[i]);
	//printf("\n");
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_read failed with return code reading Set_Switch() %d\n", ret); 
		return -1;
	}

	char result[2];
        result[0] = PACKETreceive[1];
        result[1] = PACKETreceive[2];
	return (int)(atoi(result));
}


void list_sn_all_attached() {


}

void printDeviceHookup(DeviceHookup *deviceInfo) {

	if(deviceInfo == NULL) {
		printf("NO INFO\n");
		return;
	}	

	if(deviceInfo->switchIndex == -1 || deviceInfo->portNum == -1) {
		printf("%s : No port assignment, switch_sn=%s, atten_sn=%s\n", deviceInfo->antPol,
			deviceInfo->rf_switch_sn, deviceInfo->atten_sn);
		return;
	}

	//Handle the case where there is not an attenuator attached
        char atten_sn[12];
        strcpy(atten_sn, deviceInfo->atten_sn);
	if((int)strlen(deviceInfo->atten_sn) == 0) strcpy(atten_sn, "none");
	printf("{ \"antpol\" : \"%s\", \"switch\" : %d, \"port\" : %d, \"sn\" : \"%s\", \"atten_sn\" : \"%s\" }\n", 
               deviceInfo->antPol, deviceInfo->switchIndex, 
		deviceInfo->portNum, deviceInfo->rf_switch_sn, atten_sn);
}

// ant can be the ant name (4j), or pol (4jy).
// If this is an ant name, print out info for x and y pols.
void printHookup(char *ant) {

	DeviceHookup *deviceHookup = NULL;

	if(!strcmp(ant, "all")) {
		for(int i = 0; i<NUM_RF_SWITCHES; i++) {
			for(int j = 2; j<(MAX_POLS_PER_SWITCH+2); j++) {
				if((int)strlen(ports[i][j]) == 0) continue;
				deviceHookup = getantPolHookup(ports[i][j], false);
				printDeviceHookup(deviceHookup);
				free(deviceHookup);
			}
		}
		return;
	}

	DeviceHookups *deviceHookups = getDeviceHookups(ant, false);

	if(deviceHookups == NULL) return;

	for(int i = 0; i<deviceHookups->num; i++) {

		printDeviceHookup(deviceHookups->deviceHookups[i]);

	}

}

void initDevice() {

        if(usb_defined_already == true) return;
//      if(usb_defined_already == false) return;
        usb_dev = device_init();
        if (usb_dev == NULL)
        {
                fprintf(stdout, "USB, cannot init!\n");
                cleanup(-1);
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
		ret = hid_force_open(hid, 0, &matcher, 3);
		if (ret != HID_RET_SUCCESS) {
			fprintf(stdout, "hid_force_open failed with return code %d\n", ret);
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

//IndexAndPort **getMatcherIndexes(char *ant, int *numIndexes) {
IndexAndPort **getMatcherIndexes(char **antPols, int numAntPols, int *numIndexes) {

	int nextInsertPos = 0;

	//DeviceHookups *deviceHookups = getDeviceHookups(ant, false);
	DeviceHookups *deviceHookups = getDeviceHookupsFromAntpolList(antPols, numAntPols, true);
	if(deviceHookups == NULL) return NULL;

	IndexAndPort **indexAndPort = (IndexAndPort **)calloc(deviceHookups->num, sizeof(IndexAndPort *));

	for(int i = 0; i<deviceHookups->num; i++) {
                indexAndPort[i] = (IndexAndPort *)calloc(1, sizeof(IndexAndPort));
		indexAndPort[i]->matcherIndex = -4;
		indexAndPort[i]->switchPortNum = -4;
		indexAndPort[nextInsertPos]->origListIndex = deviceHookups->deviceHookups[i]->origListIndex;
	}
	*numIndexes = deviceHookups->num;

	/*
	for(int i = 0; i<deviceHookups->num; i++) {

		printDeviceHookup(deviceHookups->deviceHookups[i]);

	}
	*/

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
			//This signifies we rab out of devices
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

			if(!strcmp(SNreceive, deviceHookups->deviceHookups[i]->rf_switch_sn)) {
				indexAndPort[nextInsertPos]->matcherIndex = matcher_index;
				indexAndPort[nextInsertPos]->switchPortNum = deviceHookups->deviceHookups[i]->portNum;
				strcpy(indexAndPort[nextInsertPos]->pn, PNreceive);
				strcpy(indexAndPort[nextInsertPos]->sn, SNreceive);
				strcpy(indexAndPort[nextInsertPos]->antPol, deviceHookups->deviceHookups[i]->antPol);
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


int main( int argc, unsigned char **argv)
{

	lock();

	if(argc > 1 && !strncmp(argv[1], "-d", 2)) {
		discoverPorts();
		cleanup(0);
	}
	else if(argc > 1 && !strncmp(argv[1], "-i", 2)) {
		if(argc != 3) {
			printHelp(); //will exit
		}
		printHookup(argv[2]);
		cleanup(0);
	}
	else {
		if(argc != 2) printHelp(); //will exit
	}

	int numAntPols = 0;
        char **antPolList = commaSepListStringToStringArray(argv[1], &numAntPols, true);
	//printArrayValues("Ant pols", antPolList, numAntPols);

	int numIndexes = -1;
	//IndexAndPort **matcherIndexes = getMatcherIndexes(argv[1], &numIndexes);
	IndexAndPort **matcherIndexes = getMatcherIndexes(antPolList, numAntPols, &numIndexes);
	//printf("NUM=%d\n", numIndexes);
	for(int i = 0; i<numIndexes; i++) {
		//printf("Index %d = %d, portnum = %d\n", i, matcherIndexes[i]->matcherIndex, matcherIndexes[i]->switchPortNum);
                matcher_try_count = 0;
		matcher_index = matcherIndexes[i]->matcherIndex;
		int switchPortNum = matcherIndexes[i]->switchPortNum;
		//printf("switchPortNum=%d\n", switchPortNum);
		initDevice();
		HIDInterfaceMatcher matcher = { VENDOR_ID, PRODUCT_ID, custom_matcher, NULL, 0 };

		ret = hid_force_open(hid, 0, &matcher, 3);
		if (ret != HID_RET_SUCCESS) {
			fprintf(stdout, "hid_force_open failed with return code %d\n", ret);
			return 1;
		}

		//char PNreceive[SEND_PACKET_LEN];
                //Get_PN(PNreceive);
                int is16 = 0;
		if(strstr(matcherIndexes[i]->pn, "16") > 0) is16 = 1;

		Set_Switch((unsigned char)switchPortNum, is16);
		//printf("Switch state: %d\n", Get_Switch(is16));
		printf("{ \"antpol\" : \"%s\", \"sn\" : \"%s\", \"pn\" : \"%s\", \"active_port\" : %d }\n",
                        matcherIndexes[i]->antPol,
			matcherIndexes[i]->sn, matcherIndexes[i]->pn, Get_Switch(is16) );
			 

		//////////////////////////////////////////////
		ret = hid_close(hid);
		if (ret != HID_RET_SUCCESS) {
			fprintf(stdout, "hid_close failed with return code %d\n", ret);
			return 1;
		}
		hid_close(hid);
	}

	hid_delete_HIDInterface(&hid);
	hid_cleanup();
	fprintf(stderr, "OK\n");
	cleanup(0);
	return 0;
}


