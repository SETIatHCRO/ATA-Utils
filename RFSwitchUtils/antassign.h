#ifndef ANTASSIGN
#define ANTASSIGN

#include <string.h>
#include <stdio.h>
#include <sys/file.h>
#include <fcntl.h>
#include <errno.h>

#define NUM_RF_SWITCHES 6
#define MAX_POLS_PER_SWITCH 16
#define RF_SWITCH_SN_INDEX 0
#define ATTEN_SN_INDEX 1

#define LOCK_FILENAME "/tmp/rf_atten_lock.txt"

int filelock_fd = -1;

// index 0 == RF switch SN
// index 1 == ATTEN SN, the attenuator hooked
char *ports[NUM_RF_SWITCHES][MAX_POLS_PER_SWITCH + 2] = {
  {"11804220007", "11807150044", "2jx", "2dx", "4kx", "1dx", "2fx", "5hx", "3jx", "3ex", "", "", "", "", "", "", "", "" },
  {"11804220005", "11807150038", "2jy", "2dy", "4ky", "1dy", "2fy", "5hy", "3jy", "3ey", "", "", "", "", "", "", "", "" },
  //{"11804220007", "", "2jx", "2dx", "4kx", "1dx", "2fx", "5hx", "3jx", "3ex", "", "", "", "", "", "", "", "" },
  //{"11804220005", "", "2jy", "2dy", "4ky", "1dy", "2fy", "5hy", "3jy", "3ey", "", "", "", "", "", "", "", "" },
  {"11807090024", "11802180076", "2ax", "2bx", "2ex", "3lx", "1fx", "5cx", "4lx", "4gx", "", "", "", "", "", "", "", "" },
  {"11807090023", "11805160031", "2ay", "2by", "2ey", "3ly", "1fy", "5cy", "4ly", "4gy", "", "", "", "", "", "", "", "" },
  {"11808230007", "11803290005", "1ax", "1bx", "1gx", "1hx", "2kx", "2mx", "3dx", "4jx", "5ex", "2cx", "4ex", "2lx", "2hx", "5bx", "5gx", ""},
  {"11808230005", "11803290019", "1ay", "1by", "1gy", "1hy", "2ky", "2my", "3dy", "4jy", "5ey", "2cy", "4ey", "2ly", "2hy", "5by", "5gy", ""}
};

typedef struct {
	char antPol[4]; //Max ant pol name would be 4 characters (includes null terminator)
        char rf_switch_sn[12];
        char atten_sn[12];
        int  switchIndex; //Starts at 0
        int  portNum; //Starts at 1
	bool isValid;
	int origListIndex;
} DeviceHookup;

typedef struct {
	int num;
	int numValid;
	DeviceHookup **deviceHookups;
} DeviceHookups;

typedef struct {
	char antPol[4]; //Max ant pol name would be 4 characters (includes null terminator)
        int matcherIndex;
        int switchPortNum;
        char pn[17];
        char sn[12];
	int origListIndex;
} IndexAndPort;

/*
#define NUM_ALL_DEVICES 9
char *pn_sn[NUM_ALL_DEVICES][2] = {
  { "USB-1SP16T-83H", "11710190006" },
  { "USB-1SP8T-63H", "11807090023" },
  { "USB-1SP8T-63H", "11804220005" },
  { "USB-1SP8T-63H", "11807090024" },
  { "USB-1SP8T-63H", "11804220007" },
  { "RUDAT-6000-30", "11803290019" },
  { "RUDAT-6000-30", "11802180076" },
  { "RUDAT-6000-30", "11805160031" },
  { "RUDAT-6000-30", "11803290005" }
};
*/

DeviceHookup *getantPolHookup(char *antPol, bool ignoreNoAtten) {

        DeviceHookup *deviceHookup = (DeviceHookup *)calloc(1, sizeof(DeviceHookup));
        strcpy(deviceHookup->antPol, antPol);
        deviceHookup->switchIndex = -1;
        deviceHookup->portNum = -1;

        for(int i = 0; i<NUM_RF_SWITCHES; i++) {
                for(int j = 2; j<(MAX_POLS_PER_SWITCH+2); j++) {
                        if(!strcmp(ports[i][j], antPol)) {

				//If no atten_sn and ignoreNoAtten==true, ignore
				if(ignoreNoAtten == true && (int)strlen(ports[i][ATTEN_SN_INDEX]) == 0) {
					continue;
				}
				deviceHookup->isValid = true;
				
				strcpy(deviceHookup->rf_switch_sn, ports[i][RF_SWITCH_SN_INDEX]);
				strcpy(deviceHookup->atten_sn, ports[i][ATTEN_SN_INDEX]);
                                deviceHookup->switchIndex = i;
                                deviceHookup->portNum = j - 1; //remember MiniCircuit port numbers start with 1
                                return deviceHookup;
                        }
                }
        }

        return deviceHookup;

}


DeviceHookups *getDeviceHookups(char *ant, bool ignoreNoAtten) {


        if((int)strlen(ant) == 2) {
                DeviceHookups *deviceHookups = (DeviceHookups *)calloc(1, sizeof(DeviceHookups));
                deviceHookups->num = 2;
                deviceHookups->deviceHookups = (DeviceHookup **)calloc(2, sizeof(DeviceHookup *));


                char antName[4];
                sprintf(antName, "%sx", ant);
                deviceHookups->deviceHookups[0] = getantPolHookup(antName, ignoreNoAtten);
		if(deviceHookups->deviceHookups[0]->isValid == true) deviceHookups->numValid++;

                sprintf(antName, "%sy", ant);
                deviceHookups->deviceHookups[1] = getantPolHookup(antName, ignoreNoAtten);
		if(deviceHookups->deviceHookups[1]->isValid == true) deviceHookups->numValid++;

                return deviceHookups;
        }
        else if((int)strlen(ant) == 3) {
                DeviceHookups *deviceHookups = (DeviceHookups *)calloc(1, sizeof(DeviceHookups));
                deviceHookups->num = 1;
                deviceHookups->deviceHookups = (DeviceHookup **)calloc(1, sizeof(DeviceHookup *));

                deviceHookups->deviceHookups[0] = getantPolHookup(ant, ignoreNoAtten);
		if(deviceHookups->deviceHookups[0]->isValid == true) deviceHookups->numValid++;
                return deviceHookups;
        }

        return NULL;
}

DeviceHookups *getDeviceHookupsFromAntpolList(char **antPols, int numAntPols, bool ignoreNoAtten) {

	DeviceHookups *deviceHookups = (DeviceHookups *)calloc(1, sizeof(DeviceHookups));
	deviceHookups->num = numAntPols;
	deviceHookups->deviceHookups = (DeviceHookup **)calloc(deviceHookups->num, sizeof(DeviceHookup *));

	int i = 0;
	for(i = 0; i<deviceHookups->num; i++) {
		deviceHookups->deviceHookups[i] = getantPolHookup(antPols[i], ignoreNoAtten);
                if(deviceHookups->deviceHookups[i]->isValid == true) deviceHookups->numValid++;
		deviceHookups->deviceHookups[i]->origListIndex = i;
	}
	return deviceHookups;
	

}

char **commaSepListStringToStringArray(char *string, int *resultLen, bool is_ant_list) {

	char *token;
	int count = 0;
	char *stringCopy = (char *)calloc(strlen(string)+1, sizeof(char));
	memcpy(stringCopy, string, strlen(string));
	char delim[2] = ",";

	token = strtok(stringCopy, delim);
	while(token != NULL) {
		count++;
		if(strlen(token) == 2) count++;
		token = strtok(NULL, delim);
	}

	int i = 0;
	int len = 0;
	memcpy(stringCopy, string, strlen(string));
	char **resultArray = (char **)calloc(count, sizeof(char *));
	token = strtok(stringCopy, delim);
        while(token != NULL) {
		resultArray[i] = (char *)calloc(4, sizeof(char));
		strcpy(resultArray[i], token);
                if(is_ant_list == true && strlen(token) == 2) {
			resultArray[i][2] = 'x';
			i++;
			resultArray[i] = (char *)calloc(4, sizeof(char));
                	strcpy(resultArray[i], token);
			resultArray[i][2] = 'y';
		}
		i++;
                token = strtok(NULL, delim);
        }

	*resultLen = i;

	return resultArray;

}

void printArrayValues(char *preamble, char **stringArray, int numValues) {

	fprintf(stdout, "%s(%d) = ", preamble, numValues);
	int i = 0;
	for(i = 0; i<numValues; i++) {
		if(i == (numValues-1))
			fprintf(stdout, "%s\n", stringArray[i]);
		else
			fprintf(stdout, "%s,", stringArray[i]);
	}

}

void lock() {

	filelock_fd = open(LOCK_FILENAME, O_RDONLY|O_CREAT);
	if(filelock_fd == -1) {
		fprintf(stderr,"ERROR: can not open lock file %s, %s exiting\n", LOCK_FILENAME, strerror(errno));
		exit(1);
	}

	bool lock_obtained = false;
	while(lock_obtained == false) {
		if(flock(filelock_fd, LOCK_EX) == -1)
			sleep(1);
		else
			lock_obtained = true;
	}

}

void cleanup(int exit_value) {

	flock(filelock_fd, LOCK_UN);
	close(filelock_fd);
        exit(exit_value);
}


#endif //ANTASSIGN

