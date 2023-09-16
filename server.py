import aiohttp
import asyncio

from datetime import datetime
import logging
import names

import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK


logging.basicConfig(level=logging.INFO)

DATE = datetime.now().date().strftime("%d.%m.%Y")
URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date=" + DATE


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    resp = await response.json()
                    return resp
                logging.error(f"Error status: {response.status} for {url}")
                return
        except aiohttp.ClientConnectionError as err:
            logging.error(f"Connection error: {str(err)}")
            return


async def get_exchange(currency: str):
    try:
        result = await request(URL)
        if result:
            for exc in result["exchangeRate"]:
                if exc["currency"] == currency:
                    return f"{currency} - buy: {exc['purchaseRateNB']}, sale: {exc['saleRateNB']}. Date: {DATE}"
        else:
            return "Failed to retrieve data"
    except Exception as e:
        logging.error(f"Error in get_exchange: {e}")
        return "Failed to retrieve data"


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def send_to_client(self, message: str, ws: WebSocketServerProtocol):
        await ws.send(message)

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            print(f"Received message: {message}")
            words = message.split()
            if message.startswith("exchange") and len(words) > 1:
                r = await get_exchange(str(words[1]).upper())
                await self.send_to_client(r, ws)

            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
