from typing import Protocol


class UnitOfWork(Protocol):
    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def commit(self):
        ...

    def rollback(self):
        ...
