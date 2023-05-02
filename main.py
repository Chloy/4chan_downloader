import asyncio as aio
from time import sleep
from downloader.fetcher import Fetcher
from downloader.downloader import Downloader


async def main():
    d = Downloader()
    d.start()
    while True:
        print('Going to parse 4chan...')
        files: list = await Fetcher('gif', ['feels']).fetch_files()
        d.add_to_queue(files)
        await aio.sleep(100)


if __name__ == '__main__':
    aio.run(main())
