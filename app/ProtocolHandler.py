import logging
import asyncio
from collections import namedtuple
from io import BytesIO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
Error = namedtuple('Error',('message',))
class ProtocolHandler():
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string,         #+ - ASCII-43
            '-': self.handle_error,                 #- - ASCII-45
            ':': self.handle_int,                   #: - ASCII-58
            '$': self.handle_string,                #$  - ASCII-36
            '*': self.handle_array,                 #* - ASCII-42
            '%': self.handle_dict,                  #% - ASCII-37
        }


    def handle_request(self, reader):
        
        first_byte = reader.read(1)
        
        if not first_byte:
            pass
        try:
            hd = self.handlers[first_byte.decode('utf-8')](reader)
            
            return hd
        except Exception as e:
            logger.error(f'bad request {e}')
    
    
    def handle_simple_string(self, reader):
        data =  reader.readline()
        ans = data.rstrip(b'\r\n')
        return  ans.decode('utf-8')

    def handle_error(self, reader):
        data =  reader.readline()

        ans = data.rstrip(b'\r\n')
        return  Error(ans)

    def handle_int(self, reader):
        data =  reader.readline()
        ans = data.rstrip(b'\r\n')
        return int(ans)

    def handle_string(self, reader):
        data =  reader.readline()

        lenght = int(data.rstrip(b'\r\n'))
        if lenght == -1:
            return None
        lenght += 2
        l_data =  reader.read(lenght)
        l_data = l_data[:-2]
        return l_data.decode('utf-8')

    def handle_array(self, reader):
        data =  reader.readline()

        num_elements = int(data.rstrip(b'\r\n'))
        print(data, num_elements)
        arr = []
        for _ in range(num_elements):
            elem =  self.handle_request(reader)  
            arr.append(elem)  
        return arr

    def handle_dict(self, reader):
        data =  reader.readline()
        num_items = int(data.rstrip(b'\r\n'))
        ellements = []
        for _ in range(num_items*2):
            elem =  self.handle_request(reader)  
            ellements.append(elem)
        return dict(zip(ellements[::2],ellements[1::2]))

    
    
    
    def write_response_noasync(self, socket_fule, data):
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        socket_fule.write(buf.getvalue())
        socket_fule.flush()

    async def write_response(self, writer, data):
        buf = BytesIO()
        self._write(buf,data)
        buf.seek(0)
        print(buf.getvalue())
        writer.write(buf.getvalue())
        await writer.drain()

    def _write(self, buf, data):

        if isinstance(data, str):
            data = bytes(data,'utf-8')


        if isinstance(data, bytes):
            buf.write(bytes('$%s\r\n%s\r\n' % (len(data), data.decode('utf-8')), 'utf-8'))
        elif isinstance(data, int):
            buf.write(bytes(':%s\r\n' % data,'utf-8'))
        elif isinstance(data, Error):
            buf.write(bytes('-%s\r\n' % error.message,'utf-8'))
        elif isinstance(data, (list, tuple)):
            buf.write(bytes('*%s\r\n' % len(data),'utf-8'))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            buf.write(bytes('%%%s\r\n' % len(data),'utf-8'))
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif data is None:
            buf.write(bytes('$-1\r\n','utf-8'))
        else:
            logger.error('err: %s' % type(data))
            raise TypeError('err: %s' % type(data))
