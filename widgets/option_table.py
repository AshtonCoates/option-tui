from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import yfinance as yf
from textual.widgets import DataTable
from textual.message import Message


@dataclass
class ContractRow:
    kind: str       # "C" / "P"
    strike: float
    last: float
    bid: float
    ask: float
    iv: float
    oi: int

    def as_row(self) -> List[str | float | int]:
        return [self.kind, self.strike, self.last, self.bid, self.ask, self.iv, self.oi]


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
        headers = ["Type", "Strike", "Last", "Bid", "Ask", "IV", "OI"]
        self.add_columns(*headers)

    async def on_chain_update(self, msg: ChainUpdate) -> None:
        """Replace all rows with the newest chain snapshot."""
        self.clear()
        self.add_rows([r.as_row() for r in msg.rows])

