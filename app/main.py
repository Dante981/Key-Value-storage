import socket
import threading
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

    

class Server:

    def __init__(self, host, port):
        self.server_address = (host, port)
        self.server_sock = None
        self.is_running = False
        #self.clients_sock = dict()


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
                    client_sock.settimeout(60)
                    #if client_address not in self.clients_sock:
                        #self.clients_sock[client_address] = client_sock

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
                data = client_sock.recv(1024)
                if not data:
                    break
                logger.info(f'Received from {client_address}: {data.decode('utf-8')}')
                client_sock.sendall(f'PONG: {data.decode('utf-8')}'.encode('utf-8'))
        
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



def main():
    SV = Server('localhost',8889)
    SV.start()

if __name__ == "__main__":
    main()
