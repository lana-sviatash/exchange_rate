from datetime import datetime, timedelta
import logging
import platform
import sys

import aiohttp
import asyncio


URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

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


async def get_exchange(date: str, currency: str):
    try:
        result = await request(URL + date)
        print(result)
        if result and "exchangeRate" in result:
            usd_rate = None
            eur_rate = None
            cur_rate = None
            
            for exc in result["exchangeRate"]:
                if exc["currency"] == "USD":
                    usd_rate = exc
                elif exc["currency"] == "EUR":
                    eur_rate = exc
                elif exc["currency"] == currency:
                    cur_rate = exc
            
            if usd_rate and eur_rate and cur_rate:
                return (f"USD - buy: {usd_rate['purchaseRate']}, sale: {usd_rate['saleRate']}. Date: {date}",
                        f"EUR - buy: {eur_rate['purchaseRate']}, sale: {eur_rate['saleRate']}. Date: {date}",
                        f"{currency} - buy: {cur_rate['purchaseRate']}, sale: {cur_rate['saleRate']}. Date: {date}")
            elif usd_rate and eur_rate:
                return (f"USD - buy: {usd_rate['purchaseRate']}, sale: {usd_rate['saleRate']}. Date: {date}",
                        f"EUR - buy: {eur_rate['purchaseRate']}, sale: {eur_rate['saleRate']}. Date: {date}")
    except Exception as e:
        logging.error(f"Error in get_exchange: {e}")

    logging.error("Failed to retrieve data")


async def main():
    try:
        try:
            days = int(sys.argv[1])
        except TypeError:
            print("Give me number of days and currency(optional)")
        dates = [datetime.now().date() - timedelta(days=i) for i in range(days)]
        formatted_dates = [date.strftime("%d.%m.%Y") for date in dates]

        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        if len(sys.argv) <= 2:
            result = await asyncio.gather(*(get_exchange(date, '') for date in formatted_dates))
            for rates_tuple in result:
                for rate in rates_tuple:
                    print(rate)
        if len(sys.argv) > 2:
            currency = str(sys.argv[2]).upper().strip()
            result = await asyncio.gather(*(get_exchange(date, currency) for date in formatted_dates))
            for rates_tuple in result:
                for rate in rates_tuple:
                    print(rate)
    except IndexError:
        print("Give me number of days and currency(optional)")


if __name__=="__main__":
    asyncio.run(main())
