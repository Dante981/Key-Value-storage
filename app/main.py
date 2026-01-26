import asyncio
import json
import re
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

    

class Server:

    def __init__(self, host, port, cl_timeout:int = 60, cl_recv:int = 1024, key_ttl:int = 30):
        self.server_address = (host, port)
        self.server = None
        self.is_running = False
        self.key_ttl = key_ttl

        self.storage = dict()
        self.ttl_key = dict()


        self.clients_sock = []

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

            welcome_message = {
                'type':'system',
                'content':'connected'
                }
            writer.write(json.dumps(welcome_message).encode('utf-8'))
            await writer.drain()

            try:
                while True:    
                    data =  await reader.read(self.cl_recv)
                    if not data:
                        break
                    data_dec = data.decode('utf-8').strip()
                    data_enc = self.pars_client_send(data_dec).encode('utf-8')
                    logger.info(f'Received from {client_addr!r}: {data_dec!r}')
                    writer.write(data_enc)
                    await writer.drain()

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
    

    def pars_client_send(self, data:str) -> str:
        ans = ''
        data_ls = [re.sub(r'\s','',x) for x in data.split(' ')]

        if len(data_ls) == 1:
            if data_ls[0].lower() == 'ping':
                ans = self.ping()
        elif len(data_ls) == 3:       
            if data_ls[0].lower() == 'set':
                key = data_ls[1]
                val = data_ls[2]
                self.set_key_storage(key,val)
        elif len(data_ls) == 2:
            if data_ls[0].lower() == 'get':
                ans = self.get_key_storage(data_ls[1])
                
        return ans

    async def ttl_check(self):       
        while self.is_running:
            try:
                current_time = asyncio.get_event_loop().time()
                del_keys = []
                for key, timestart in self.ttl_key.items():
                    if current_time - timestart >= self.key_ttl:
                        del_keys.append(key)

                for key in del_keys:
                        logger.info(f'del key:{key} val:{self.storage[key]}')
                        self.ttl_key.pop(key, None)
                        self.storage.pop(key, None)                             
            except Exception as e:
                logger.error(f'TTL check error: {e}')
            await asyncio.sleep(0.5)

            
            


    
    def set_key_storage(self, key, value):
        time_start = asyncio.get_event_loop().time()
        self.storage[key] = value
        self.ttl_key[key] = time_start


    def get_key_storage(self,key):
        if key in self.storage:
            return f'key:{key} val:{self.storage[key]} ttl:{time.time() - self.ttl_key[key]} \r\n'
        return 'key not found\r\n'

    def ping(self):
        return 'PONG\r\n'



def main():
    SV = Server('localhost',8889)
    asyncio.run(SV.start())

if __name__ == "__main__":
    main()
