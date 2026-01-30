from ProtocolHandler import ProtocolHandler
from collections import namedtuple
import socket

Error = namedtuple('Error',('message',))

class Client:
    
    def __init__(self, host='localhost', port=8889):

        self.protocol = ProtocolHandler()
        self.cl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cl_socket.connect((host,port))
        self.fh = self.cl_socket.makefile('rwb')


    def execute(self, *args):
        self.protocol.write_response_noasync(self.fh, args)
        resp =  self.protocol.handle_request(self.fh)
        if isinstance(resp, Error):
            raise TypeError(resp.message)
        return resp

    def get(self, key):
        return  self.execute('GET', key)
    
    def set(self, key, value):
        return  self.execute('SET', key, value)

    def delete(self, key):
        return  self.execute('DELETE', key)

    def flush(self):
        return  self.execute('FLUSH')
    
    def mget(self, *keys):
        return  self.execute('MGET', *keys)

    def mset(self, *items):
        return  self.execute('MSET', *items)


