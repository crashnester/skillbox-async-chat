#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from collections import deque

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
            self.server.history.append(f"{self.login}: {decoded}\r\n")
            for _ in range(10, len(self.server.history)) :
                self.server.history.popleft()
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                login_counter = 0
                for user in self.server.clients :
                    if self.login == user.login :
                        login_counter += 1
                if login_counter > 1 :
                    self.transport.write("Такой логин уже зарегистрирован\r\n".encode())
                    self.transport.close()
                else :
                    self.transport.write(f"Привет, {self.login}!\r\n".encode())
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\r\n".encode())

    def send_history(self):
        for i in range(len(self.server.history)) :
            self.transport.write(self.server.history[i].encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = deque()

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
