import requests


class ATARestException(Exception):
    """
    Base exception for any ATA REST related problems
    """
    pass


class ATARest:
    """
    Simple API to encapsulate REST calls with more directed error handling.
    Any errors will cause a ATARestException to be thrown with any error message
    if available.
    """
    
    HOST = 'restgw.hcro.org'
    PORT = 12345

    RETURN_MSG_KEY = 'message'

    _OP_GET = 'get'
    _OP_PUT = 'put'
    _OP_DEL = 'delete'

    _debug = False

    @classmethod
    def form_url(cls, endpoint):
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = 'http://{:s}:{:d}{:s}'.format(cls.HOST, cls.PORT, endpoint)
        return url

    @classmethod
    def _do_op(cls, op, endpoint, **kwargs):
        """
        Handle one of the HTTP operations

        :param op: HTTP operation to perform
        :param endpoint: REST endpoint (no stem) to call
        :param kwargs: any additional arguments to requests.get(), etc.
        
        :returns dict from JSON section of REST server response
        :rtype dict

        :raises ATARestException on any error response
        """

        try:
            url = cls.form_url(endpoint)
            if cls._debug:
                print(url)

            if op == cls._OP_GET:
                response = requests.get(url, **kwargs)
            elif op == cls._OP_PUT:
                response = requests.put(url, **kwargs)
            elif op == cls._OP_DEL:
                response = requests.delete(url, **kwargs)
            else:
                raise ATARestException('Bad op given to ATARest._do_op()')

            json = response.json()
            if response.status_code != requests.codes.ok:
                if json and cls.RETURN_MSG_KEY in json:
                    raise ATARestException(json[cls.RETURN_MSG_KEY])
                else:
                    raise ATARestException('No error message from REST API ' + op)
            if cls._debug:
                print(json)
            return json
        except Exception as e:
            raise ATARestException(str(e))


    @classmethod
    def get(cls, endpoint, **kwargs):
        """
        HTTP GET operation on ATA REST API endpoint

        :param endpoint: REST endpoint (no stem) to call
        :param kwargs: any additional arguments to requests.get(), etc.

        :returns dict from JSON section of REST server response
        :rtype dict

        :raises ATARestException on any error response
        """
        return cls._do_op(cls._OP_GET, endpoint, **kwargs)

    @classmethod
    def put(cls, endpoint, **kwargs):
        """
        HTTP PUT operation on ATA REST API endpoint

        :param endpoint: REST endpoint (no stem) to call
        :param kwargs: any additional arguments to requests.get(), etc.

        :returns dict from JSON section of REST server response
        :rtype dict

        :raises ATARestException on any error response
        """
        return cls._do_op(cls._OP_PUT, endpoint, **kwargs)

    @classmethod
    def delete(cls, endpoint, **kwargs):
        """
        HTTP DELETE operation on ATA REST API endpoint

        :param endpoint: REST endpoint (no stem) to call
        :param kwargs: any additional arguments to requests.get(), etc.

        :returns dict from JSON section of REST server response
        :rtype dict

        :raises ATARestException on any error response
        """
        return cls._do_op(cls._OP_DEL, endpoint, **kwargs)
    

if __name__ == '__main__':
    print(ATARest.get('/antennas/1a/pams'))

