from typing import TypedDict
from itertools import chain
import asyncio as aio
import aiohttp
import re
from subprocess import run, PIPE
from pathlib import Path


_4CHAN_URL = 'https://boards.4chan.org/'
true = True
false = False
global_tasks: list[aio.Task]


ALLOWED_TYPES = [
    'webm',
    'gif',
    'jpeg',
    'png',
]


def check_file(path: Path):
    assert path.exists() is True
    file_type = run(
        [
            'file',
            str(path)
        ],
        stdout=PIPE,
    ).stdout
    file_type = file_type.decode().removeprefix(f'{path}: ').lower().strip()
    return any(file_type.startswith(allowed_type) for allowed_type in ALLOWED_TYPES)


class FileURI(TypedDict):
    uri: str
    tags: list[str]
    board: str


class Thread(TypedDict):
    uri: str
    tags: list[str]
    board: str


class Fetcher:
    def __init__(self, board: str, tags: list[str]):
        self._tags = tags
        self._board = board
        self._board_url = f'{_4CHAN_URL}{self._board}'
        self._session: aiohttp.ClientSession

    async def fetch_files(self):
        async with aiohttp.ClientSession() as session:
            self._session = session
            matched_threads = await self._get_matched_threads()
            tasks = [
                aio.create_task(self._get_files_from_thread(thread))
                for thread in matched_threads
            ]
            await aio.gather(*tasks)
            res = []
            for task in tasks:
                res.extend(task.result())
            return res

    async def _get_files_from_thread(self, thread: Thread) -> list[FileURI]:
        async with self._session.get(thread['uri']) as resp:
            resp_text = await resp.text()
        offset = 0
        files = []
        while True:
            try:
                match = re.search(
                    r'//i\.4cdn\.org/[0-9a-zA-Z/.]+((webm)|(gif)|(jpg)|(png)|(jpeg))',
                    resp_text[offset:]
                )
                offset += match.span()[0] + len(match[0])
            except (AttributeError, TypeError):
                # print(f'All files for {title}')
                break
            file = FileURI(uri=f'https:{match[0]}', tags=thread['tags'], board=thread['board'])
            if file not in files and not match[0].split('.')[-2].endswith('s'):
                files.append(file)

        return files

    async def _get_matched_threads(self) -> list[Thread]:
        async with self._session.get(f'{self._board_url}/catalog') as resp:
            text = await resp.text()
        # print('Got catalog')
        threads_json: dict[str, dict] = eval(
            text
            .split('var catalog = ')[-1]
            .split(';var style_group = ')[0]
        )['threads']
        matched_threads = []
        for thread, meta in threads_json.items():
            tags_intersection = [tag for tag in self._tags if tag.lower() in meta['teaser'].lower()+meta['sub'].lower()]
            if tags_intersection:
                matched_threads.append(
                    Thread(
                        uri=f'{self._board_url}/thread/{thread}',
                        tags=tags_intersection,
                        board=self._board
                    )
                )

        return matched_threads
