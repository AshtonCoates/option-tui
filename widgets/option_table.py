from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from textual.widgets import DataTable
from textual.message import Message


@dataclass
class ContractRow:
    call_iv: float
    # call_oi: int
    call_last: float
    call_bid: float
    call_ask: float
    strike: float
    put_ask: float
    put_bid: float
    put_last: float
    # put_oi: int
    put_iv:float

    def as_row(self) -> List[str | float | int]:
        row = [
            self.call_iv,
            # self.call_oi,
            self.call_last,
            self.call_bid,
            self.call_ask,
            self.strike,
            self.put_ask,
            self.put_bid,
            self.put_last,
            # self.put_oi,
            self.put_iv
        ]

        return row


class ChainUpdate(Message):
    """Posted by a worker when fresh chain data arrives."""
    def __init__(self, rows: Iterable[ContractRow], timestamp: datetime) -> None:
        self.rows = list(rows)
        self.timestamp = timestamp
        super().__init__()


class OptionTable(DataTable):
    """DataTable pre-configured for option chains."""

    zebra_stripes = True
    cursor_type = "row"

    def on_mount(self) -> None:
        headers = ["C IV", "C Last", "C Bid", "C Ask",
                   "Strike", "P Ask", "P Bid", "P Last", "P IV"]
        self.add_columns(*headers)

    async def on_chain_update(self, msg: ChainUpdate) -> None:
        """Replace all rows with the newest chain snapshot."""
        self.clear()
        self.add_rows([r.as_row() for r in msg.rows])