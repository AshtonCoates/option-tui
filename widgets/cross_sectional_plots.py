import numpy as np

from textual_plotext import PlotextPlot
from widgets.option_table import ChainUpdate


class ImpliedVolPlot(PlotextPlot):
    """Plot for implied volatility of options."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Implied Volatility"
        self.xlabel = "Strike Price"
        self.ylabel = "Implied Volatility (%)"
        self.xgrid = True
        self.ygrid = True
        self.show_legend = True

    async def fit_curve(self, call_ivs, strikes) -> np.ndarray:
        "Fit a degree 4 polynomial to the implied volatility data"
        coeffs = np.polyfit(strikes, call_ivs, 4)
        return np.polyval(coeffs, strikes)

    async def on_chain_update(self, msg: ChainUpdate) -> None:
        self.plt.clear_data()
        x = [msg.rows[i].strike for i in range(len(msg.rows))]
        y = [msg.rows[i].call_iv for i in range(len(msg.rows))]
        call_ivs = await self.fit_curve(y, x)
        self.plt.scatter(call_ivs, y)
        self.plt.title(self.title)
        self.plt.xlabel(self.xlabel)
        self.plt.ylabel(self.ylabel)
        self.refresh()
