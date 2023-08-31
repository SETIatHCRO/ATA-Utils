import redis
import time

REDISHOST = 'redishost'
REDIS = redis.Redis(REDISHOST)
SLEEP_TIME = 0.1
NSEC       = 4. #to retry getting lock
MAX_NTRIES = int(NSEC/SLEEP_TIME)
DEFAULT_EXPIRE = 3 #time in seconds afterwhich lock will expire

LOCK_ON  = b'1'


class LockError(Exception):
    pass


try:
    REDIS.ping()
except ConnectionError as e:
    raise



def set_device_lock(device_hostname,expire=DEFAULT_EXPIRE):
    
    ntries = 0
    lockname = device_hostname + "_lock"

    while ntries < MAX_NTRIES:
        set_result = REDIS.set(lockname, LOCK_ON, ex = expire, nx = True)
        if set_result:
            return 1
        else:
            time.sleep(SLEEP_TIME)

    raise LockError("Lock for device '%s' couldn't be obtained "
                        "after %i tries" %(device_hostname, ntries))

    '''
    lockname = device_hostname+"_lock"

    lock = REDIS.get(lockname)
    ntries = 0
    if lock:
        # make sure we can obtain lock
        while lock:
            lock = REDIS.get(lockname)
            time.sleep(0.1)
            ntries += 1
            if ntries > MAX_NTRIES:
                raise LockError("Lock for device '%s' couldn't be obtained "
                        "after %i tries" %(device_hostname, ntries))

        # now set lock
        resp = REDIS.set(lockname, LOCK_ON, ex=expire)
        if resp:
            return 1
        else:
            raise LockError("Could not set lock %s"
                    %lockname)

    else:
        resp = REDIS.set(lockname, LOCK_ON, ex=expire)
        if resp:
            return 1
        else:
            raise LockError("Could not set lock %s (was initially unset)"
                    %lockname)
    '''


def release_device_lock(device_hostname):
    lockname = device_hostname+"_lock"

    resp = REDIS.delete(lockname)
    return resp
