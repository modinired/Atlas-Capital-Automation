
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Any as _Any3, Dict as _Dict3

class Agent(_ABC):
    name: str

    @_abstractmethod
    async def run(self, payload: _Dict3[str, _Any3]) -> _Dict3[str, _Any3]:
        ...
