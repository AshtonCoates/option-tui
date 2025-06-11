import asyncio
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header
from textual.worker import WorkerFailed
from textual_plotext import PlotextPlot
from wakepy import keep

from widgets.option_table import ChainUpdate, ContractRow, OptionTable
from widgets.cross_sectional_plots import ImpliedVolPlot

SYMBOL       = "^SPX"
REFRESH_SEC  = 30
EXPIRY_PICK  = 1            # 0 = nearest expiry, 1 = next-nearest …


class OptionsDash(App):
    TITLE     = f"{SYMBOL} options chain"
    CSS_PATH  = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield OptionTable(id='chain')
        with Container(id='cross_sectional_plot'):
            yield ImpliedVolPlot(id='implied_vol_plot')
        yield Footer()

    # ---------- background worker ----------
    async def _poll_chain(self) -> None:

        ticker = yf.Ticker(SYMBOL)
        while True:
            try:
                expiries = ticker.options
                expiry   = expiries[EXPIRY_PICK]
                opt_chain = ticker.option_chain(expiry)

                # reformat the data to list puts and calls together
                calls = opt_chain.calls
                puts = opt_chain.puts
                
                option_data = pd.merge(
                    calls, puts, on='strike', suffixes=('_call', '_put')
                )

                # keep only 25 rows each side of the ATM strike
                option_data['mid_call'] = (option_data['bid_call'] + option_data['ask_call']) / 2
                option_data['mid_put'] = (option_data['bid_put'] + option_data['ask_put']) / 2
                option_data['diff'] = np.abs(option_data['mid_call'] - option_data['mid_put'])
                atm_index = option_data['diff'].idxmin()
                option_data = option_data.iloc[max((0, atm_index-25)):atm_index+26]
                
                rows = []
                for _, row in option_data.iterrows():
                    rows.append(
                        ContractRow(
                            row.impliedVolatility_call,
                            row.lastPrice_call, row.bid_call, row.ask_call,
                            row.strike,
                            row.ask_put, row.bid_put, row.lastPrice_put,
                            row.impliedVolatility_put
                        )
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

    async def on_chain_update(self, msg: ChainUpdate) -> None:
        """Update the table with new chain data."""
        self.query_one("#chain", OptionTable).post_message(msg)
        # self.query_one("#implied_vol_plot", ImpliedVolPlot).post_message(msg)
        
        

if __name__ == "__main__":
    with keep.presenting():
        OptionsDash().run()

