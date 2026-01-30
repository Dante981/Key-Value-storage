import asyncio
import json
import re
import logging
import time
from io import BytesIO
from collections import namedtuple
from ProtocolHandler import ProtocolHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
Error = namedtuple('Error',('message',))
    

class Server:

    def __init__(self, host, port, cl_timeout:int = 60, cl_recv:int = 1024, key_ttl:int = 30):
        self.server_address = (host, port)
        self.server = None
        self.is_running = False
        self.key_ttl = key_ttl
        self.REST = ProtocolHandler()
        self.storage = dict()
        self.ttl_key = dict()


        self.clients_sock = []

        self.commands = {
            "GET": self._get,
            "SET": self._set,
            "DELETE": self._delete,
            "FLUSH": self._flush,
            "MGET": self._mget,
            "MSET": self._mset,
        }

        self.cl_timeout = cl_timeout
        self.cl_recv = cl_recv


    async def start(self):
        
        self.server = await asyncio.start_server(
        self.handle_client, self.server_address[0], self.server_address[1])
            
        addr = self.server.sockets[0].getsockname()
        logger.info(f'server {addr} online ') 
        self.is_running = True
        try:
            server_task = asyncio.create_task(self.server.serve_forever())
            ttl_task = asyncio.create_task(self.ttl_check())
            await server_task

        except KeyboardInterrupt:
            logger.info('server off')
        except Exception as e:
            logger.error(f'server err {e}')
        finally:
            self.stop()
            if ttl_task:
                ttl_task.cancel()


    async def handle_client(self, reader, writer):
            client_addr = writer.get_extra_info('peername')
            logger.info(f'Processing client {client_addr[0]}:{client_addr[1]}')
                
            self.clients_sock.append(writer)

            try:
                while True:   


                    data =  await reader.read(1024)
                    logger.info(f'Received from {client_addr!r}: {data!r}')
                    logger.info(f'data {data}')
                    if not data:
                        break

                    buf = BytesIO(data)
                    

                    data = self.REST.handle_request(buf)
                    logger.info(f'Received from {client_addr!r}: {data!r}')
                    
                    resp = self.get_response(data)

                    await self.REST.write_response(writer,resp)

            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f'{e}')
            finally:
                if writer in self.clients_sock:
                    self.clients_sock.remove(writer)
                writer.close()
                await writer.wait_closed() 
                logger.info(f"{client_addr} disconnect")

    
    def stop(self):
        self.is_running = False
        if self.server:
            self.server.close()
            logger.info(f'Server close {self.server_address[0]}:{self.server_address[1]}')

    
    async def ttl_check(self):       
        while self.is_running:
            try:
                current_time = asyncio.get_event_loop().time()
                del_keys = []
                for key, timestart in self.ttl_key.items():
                    #print(key, current_time - timestart)
                    if current_time - timestart >= self.key_ttl:
                        del_keys.append(key)

                for key in del_keys:
                        logger.info(f'del key:{key} val:{self.storage[key]}')
                        self.ttl_key.pop(key, None)
                        self.storage.pop(key, None)                             
            except Exception as e:
                logger.error(f'TTL check error: {e}')
            await asyncio.sleep(0.5)

    
    def get_response(self, data):
        if not isinstance(data, list):
            try:
                data = data.split()
            except:
                logger.error('Request must be list or simple string')
                raise TypeError('Request must be list or simple string')

        if not data:
            logger.error('Missing command')
            raise TypeError('Missing command')


        command = data[0].upper()
        if command not in self.commands:
            logger.error('Unrecognized command: %s' % command)
            raise TypeError('Unrecognized command: %s' % command)

        return self.commands[command](*data[1:])

    def _get(self, key):
        return self.storage[key]

    def _set(self, key, value):
        time_ttl = asyncio.get_event_loop().time()
        self.storage[key] = value
        self.ttl_key[key] = time_ttl
        return 1
    
    def _delete(self, key):
        if key in self.storage:
            del self.storage[key]
            del self.ttl_key[key]
            return 1
        return 0

    def _flush(self):
        stlen = len(self.storage)
        self.storage.clear()
        self.ttl_key.clear()
        return stlen

    def _mget(self, *keys):
        return [self.storage.get(key) for key in keys]

    def _mset(self, *items):
        time_ttl = asyncio.get_event_loop().time()
        data = zip(items[::2], items[1::2])

        for key, value in data:
            print(key,value)
            self.storage[key] = value
            self.ttl_key[key] = time_ttl
        return len(list(data))

            



def main():
    SV = Server('localhost',8889)
    asyncio.run(SV.start())

if __name__ == "__main__":
    main()
