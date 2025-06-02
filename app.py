import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Container
from textual.worker import WorkerFailed

from widgets.option_table import OptionTable, ChainUpdate, ContractRow

SYMBOL       = "AAPL"
REFRESH_SEC  = 30
EXPIRY_PICK  = 0            # 0 = nearest expiry, 1 = next-nearest …


class OptionsDash(App):
    TITLE     = f"{SYMBOL} options chain"
    CSS_PATH  = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            self.table = OptionTable(id="chain")
            yield self.table
        yield Footer()

    # ---------- background worker ----------
    async def _poll_chain(self) -> None:
        import yfinance as yf  # import inside thread still OK

        ticker = yf.Ticker(SYMBOL)
        while True:
            try:
                expiries = ticker.options
                expiry   = expiries[EXPIRY_PICK]
                opt_chain = ticker.option_chain(expiry)

                rows = []
                for _, row in opt_chain.calls.iterrows():
                    rows.append(
                        ContractRow("C", row.strike, row.lastPrice,
                                    row.bid, row.ask, row.impliedVolatility,
                                    row.openInterest)
                    )
                for _, row in opt_chain.puts.iterrows():
                    rows.append(
                        ContractRow("P", row.strike, row.lastPrice,
                                    row.bid, row.ask, row.impliedVolatility,
                                    row.openInterest)
                    )

                self.post_message(ChainUpdate(rows, datetime.utcnow()))

            except Exception as exc:
                await self.post_message(
                    ChainUpdate([], datetime.utcnow())
                )
                self.notify(f"Fetch error: {exc}", severity="error")

            await asyncio.sleep(REFRESH_SEC)

    async def on_mount(self) -> None:
        # run in a *thread* (yfinance is blocking / network I/O)
        self.run_worker(self._poll_chain, thread=True, name="yahoo")

    # optional: show a toast if worker dies permanently
    async def on_worker_failed(self, e: WorkerFailed) -> None:
        self.notify(f"Worker crashed: {e.error}", severity="error")


if __name__ == "__main__":
    OptionsDash().run()

