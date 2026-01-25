import socket
import threading
import re
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

    

class Server:

    def __init__(self, host, port, sv_listen:int = 10, cl_timeout:int = 60, cl_recv:int = 1024):
        self.server_address = (host, port)
        self.server_sock = None
        self.sv_listen = sv_listen
        self.is_running = False


        self.clients_sock = dict()

        self.cl_timeout = cl_timeout
        self.cl_recv = cl_recv


    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(self.server_address)
        self.server_sock.listen(10)
        logger.info(f'Server start {self.server_address[0]}:{self.server_address[1]}')
        self.is_running = True

        try:
            while self.is_running:
                try:
                    client_sock, client_address = self.server_sock.accept()
                    self.clients_sock[client_address] = client_sock
                    client_sock.settimeout(self.cl_timeout)

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args= (client_sock, client_address)
                    ) 
                    client_thread.daemon = True
                    client_thread.start()

                    logger.info(f'online: {threading.active_count() - 1}')
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.is_running:
                        logger.error(f'er connect: {s}')
                        break
        except KeyboardInterrupt:
            logger.info('server off')
        except Exception as e:
            logger.error(f'server err {e}')
        finally:
            self.stop()
            

    def handle_client(self, client_sock, client_address):
        try:
            logger.info(f'Processing client {client_address}')
            while True:
                data = client_sock.recv(self.cl_recv)
                if not data:
                    break
                try:
                    data_dec = data.decode('utf-8')
                    data_enc = self.pars_client_send(data_dec).encode('utf-8')
                    logger.info(f'Received from {client_address}: {data_dec}')
                    client_sock.send(data_enc)
                    
                except Exception as e:
                    logger.error(f'Code err: {e}')
        except ConnectionResetError:
            logger.error(f"{client_address} disconnect")
        except socket.timeout:
            logger.error(f"timeout: {client_address}")
        except Exception as e:
            logger.error(f'Er client {client_address}: {e}')
        finally:
            client_sock.close()
            logger.info(f"disconnect: {client_address}")

    
    
    def stop(self):
        self.is_running = False
        if self.server_sock:
            self.server_sock.close
            logger.info(f'Server close {self.server_address[0]}:{self.server_address[1]}')
    

    def pars_client_send(self, data:str) -> str:
        ans = ''
        data_ls = [re.sub(r'\s','',x) for x in data.split(' ')]
        print(data_ls)
        if len(data_ls) > 0:
            if data_ls[0].lower() == 'ping':
                ans = self.ping()
        return ans

    
    
    def ping(self):
        return 'PONG\r\n'



def main():
    SV = Server('localhost',8889)
    SV.start()

if __name__ == "__main__":
    main()
