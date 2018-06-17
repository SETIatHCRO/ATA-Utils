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

void printHelp() {

	fprintf(stderr, "Minicircuits rf switch controller. PN: USB-1SP8T-63H\n\n");
	fprintf(stderr, "rfswitch <state> <rf switch number>\n");
        fprintf(stderr, "  state = \n");
	fprintf(stderr, "    -1 to print out the serial number and part number only, then exits.\n");
	fprintf(stderr, "    -2 to print out the switch number that is active, then exits.\n");
        fprintf(stderr, "    1 .. 8, turn on a switch, turn the others off\n");
        fprintf(stderr, "  rf switch number (as of June 06, 2018)\n");
        fprintf(stderr, "    0 == left unit, SN: 1180422005\n");
        fprintf(stderr, "    1 == right unit, SN: 1180422007\n");
        fprintf(stderr, "    (they are labeled below each unit)\n");
	fprintf(stderr, "Will print OK\\n of successful. Otherwise an error will be reported.\n");
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
void Set_Switch ( unsigned char state)
{
	int i = 0;
        char PACKETreceive[SEND_PACKET_LEN];
        PACKET[0] = 1;
        sprintf(PACKET+1, ":SP8T:STATE:%d", state);
	ret = hid_interrupt_write(hid, 0x01, PACKET, SEND_PACKET_LEN,1000);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_write failed with return code, sending Set_Switch() %d\n", ret);
	}
	memset(PACKETreceive, 0, sizeof(PACKETreceive));
	ret = hid_interrupt_read(hid, 0x01, PACKETreceive, SEND_PACKET_LEN,1000);
	//for(i=0;i<16; i++) printf("[%d,%c]", PACKETreceive[i], PACKETreceive[i]);
	//for(i=0;i<16; i++) printf("[%c]", PACKETreceive[i]);
	//printf("\n");
	// Read packet Packetreceive[0]=1
	if (ret != HID_RET_SUCCESS) {
		fprintf(stderr, "hid_interrupt_read failed with return code reading Set_Switch() %d\n", ret); }
}

int Get_Switch ()
{
        int i = 0;
        char PACKETreceive[SEND_PACKET_LEN];

        PACKET[0] = 1;
        sprintf(PACKET+1, ":SP8T:STATE?");
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

	return (int)(PACKETreceive[1] - 48);
}


void list_sn_all_attached() {


}

int main( int argc, unsigned char **argv)
{

	if(argc != 3) printHelp(); //will exit

	matcher_index = atoi(argv[2]);
	usb_dev = device_init();
	if (usb_dev == NULL)
	{
		fprintf(stdout, "Device not found!\n");
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
		fprintf(stdout, "hid_init failed with return code %d\n", ret);
		return 1;
	}
	hid = hid_new_HIDInterface();
	if (hid == 0) {
		fprintf(stdout, "hid_new_HIDInterface() failed, out of memory?\n");
		return 1;
	}

	ret = hid_force_open(hid, 0, &matcher, 3);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stdout, "hid_force_open failed with return code %d\n", ret);
		return 1;
	}

	////////////// Switching //////////////////
	if(atoi(argv[1]) == -1) {
	  char PNreceive[SEND_PACKET_LEN];
	  char SNreceive[SEND_PACKET_LEN];
	  int StrLen1;
	  Get_PN(PNreceive);
	  fprintf(stdout," PN= %s .\n",PNreceive);
	  Get_SN(SNreceive);
	  fprintf(stdout," SN= %s .\n",SNreceive);
	  exit(0);
	}

	if(atoi(argv[1]) >= 0) {
		Set_Switch((unsigned char)atoi(argv[1]));
	}
	else if(atoi(argv[1]) == -2) {
	  printf("Switch state: %d\n", Get_Switch());
	}

	//////////////////////////////////////////////
	ret = hid_close(hid);
	if (ret != HID_RET_SUCCESS) {
		fprintf(stdout, "hid_close failed with return code %d\n", ret);
		return 1;
	}
	hid_delete_HIDInterface(&hid);
	ret = hid_cleanup();
	if (ret != HID_RET_SUCCESS) {
		fprintf(stdout, "hid_cleanup failed with return code %d\n", ret);
		return 1;
	}

	printf("OK\n");
	return 0;
}


