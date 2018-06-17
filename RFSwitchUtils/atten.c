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

void printHelp() {

        fprintf(stderr, "Minicircuits attenuator. PN: RUDAT-6000-30\n\n");
        fprintf(stderr, "atten <dB> <rf switch number>\n");
        fprintf(stderr, "  attenuation, in dB 0.0 to 31.75\n");
        fprintf(stderr, "    -1 will print out the part number and serial number then exit.\n");
        fprintf(stderr, "  attenuator number (as of June 06, 2018)\n");
        fprintf(stderr, "    0 == left unit, SN: 11803290005\n");
        fprintf(stderr, "    1 == right unit, SN: 11803290019\n");
        fprintf(stderr, "    (they are labeled below each unit)\n");
        fprintf(stderr, "Will print OK,<atten read from unit, dB>\\n if successful. Otherwise an error will be reported.\n");
        fprintf(stderr, "**REMEMBER to run as root!!**\n");
        exit(0);

}

bool custom_matcher(struct usb_dev_handle const* usbdev,
    void* custom, unsigned int len) {

        struct usb_device const* dev = usb_device((usb_dev_handle*)usbdev);
        //printf("PRODUCT_ID=%X\n", PRODUCT_ID);
        //printf("Matcher... %X, %X\n", dev->descriptor.idVendor, dev->descriptor.idProduct);
        if(dev->descriptor.idVendor == VENDOR_ID && dev->descriptor.idProduct == PRODUCT_ID) {
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
void ReadAtt (char* AttStr)
{
	int i;

	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=18; // Ruturn attenuation code
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code %d\n", ret);
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
		fprintf(stderr, "hid_interrupt_read failed with return code %d\n", ret); }
}

void Set_Attenuation (unsigned char **AttValue)
{
	int i;
	char PACKETreceive[SEND_PACKET_LEN];
	PACKET[0]=19; // Set Attenuation code is 19.
	PACKET[1]= (int)atoi(AttValue[1]);
	float t1=(float)(atof(AttValue[1]));
	PACKET[2]= (int) ((t1-PACKET[1])*4);
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code %d\n", ret);
	}
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	// Read packet Packetreceive[0]=1
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_read failed with return code %d\n", ret); }
}
int main( int argc, unsigned char **argv)
{
	if(argc != 3) printHelp(); //will exit

	matcher_index = atoi(argv[2]);

	char AttValue[3];
	float LastAtt=0.0;
	usb_dev = device_init();
	if (usb_dev == NULL)
	{
		fprintf(stderr, "Device not found!\n");
		exit(-1);
	}
	if (usb_dev != NULL)
	{
		usb_handle = usb_open(usb_dev);
		int drstatus = usb_get_driver_np(usb_handle, 0, kdname, sizeof(kdname));
		if (kdname != NULL && strlen(kdname) > 0) {
			usb_detach_kernel_driver_np(usb_handle, 0);
		}
	}
	usb_reset(usb_handle);
	usb_close(usb_handle);
	HIDInterfaceMatcher matcher = { VENDOR_ID, PRODUCT_ID, custom_matcher, NULL, 0 };
	ret = hid_init();
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_init failed with return code %d\n", ret);
		return 1;
	}
	hid = hid_new_HIDInterface();
	if (hid == 0) {
		fprintf(stderr, "hid_new_HIDInterface() failed, out of memory?\n");
		return 1;
	}

	ret = hid_force_open(hid, 0, &matcher, 3);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_force_open failed with return code %d\n", ret);
		return 1;
	}
	if(atoi(argv[1]) < 0) {
		char PNreceive[SEND_PACKET_LEN];
		char SNreceive[SEND_PACKET_LEN];
		int StrLen1;
		Get_PN(PNreceive);
		fprintf(stderr," PN= %s .\n",PNreceive);
		Get_SN(SNreceive);
		fprintf(stderr," SN= %s .\n",SNreceive);
		exit(0);
	}
	Set_Attenuation(argv); // set attenuation
	ReadAtt ( AttValue);
	LastAtt=(int)(AttValue[0])+(float)(AttValue[1])/4;
	ret = hid_close(hid);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_close failed with return code %d, atten read was %f db\n", ret, LastAtt);
		return 1;
	}
	hid_delete_HIDInterface(&hid);
	ret = hid_cleanup();
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_cleanup failed with return code %d, atten read was %f db\n", ret, LastAtt);
		return 1;
	}
	fprintf(stderr,"OK,%f\n",LastAtt);
	return 0;
}
