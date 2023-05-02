import requests
from threading import Thread
from queue import Queue, Empty
from time import sleep
from pathlib import Path
from downloader.fetcher import FileURI
from downloader.db import DB


class Downloader(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self._active = True
        self._download_queue = Queue()
        self._db = DB()

    def run(self):
        while self._active:
            print(f'Downloader queue size {self._download_queue.qsize()}')
            try:
                file: FileURI = self._download_queue.get_nowait()
            except Empty:
                print(f'Downloader queue empty, wait 10 sec')
                sleep(10)
                continue
            filename = file['uri'].rsplit('/', 1)[1]
            if self._db.is_file_exists(filename):
                print(f'{file["uri"]} already downloaded, skip.')
                continue
            response = requests.get(file['uri'])
            if response.status_code == 200:
                filepath = Path(f'../downloaded/{file["board"]}/{"I".join(file["tags"])}/{file["uri"].rsplit("/", 1)[1]}')
                print(f'Got element {file["uri"]}, going to download it to {filepath}.')
                if not filepath.parent.exists():
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_bytes(response.content)
                self._db.add_file(filename, str(filepath), '')

    def add_to_queue(self, elements: list[FileURI]):
        if not isinstance(elements, list):
            elements = [elements]
        for elem in elements:
            self._download_queue.put_nowait(elem)

    def stop(self):
        self._active = False
