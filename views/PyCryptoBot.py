from rich.table import Text
from rich.table import Table
from rich.console import Console
from datetime import datetime


class RichText:
    @staticmethod
    def notify(notification: str = "", app: object = None, level: str = "normal") -> None:
        if notification == "":
            return

        if level == "warning":
            color = "dark_orange"
        elif level == "error":
            color = "red1"
        elif level == "critical":
            color = "red1 blink"
        else:
            color = "violet"

        table_console = Table(title=None, box=None, show_header=False, show_footer=False)
        table_console.add_row(
            RichText.styled_text("Bot1", "magenta"),
            RichText.styled_text(datetime.today().strftime("%Y-%m-%d %H:%M:%S"), "white"),
            RichText.styled_text(app.market, "yellow"),
            RichText.styled_text(str(app.granularity.to_integer), "yellow"),
            RichText.styled_text(notification, color),
        )
        console_term = Console()
        console_term.print(table_console)
        if app.disablelog is False:
            app.console_log.print(table_console)

    @staticmethod
    def action_text(action: str = "WAIT") -> Text:
        if action == "":
            return None

        action_msg = f"Action: {action}"

        text = Text(action_msg)
        text.stylize("white", 0, 7)
        text.stylize("cyan", 8, len(action_msg))
        return text

    @staticmethod
    def last_action_text(action: str = "WAIT") -> Text:
        if action == "":
            return None

        action_msg = f"Last Action: {action}"

        text = Text(action_msg)
        text.stylize("white", 0, 12)
        text.stylize("cyan", 13, len(action_msg))
        return text

    @staticmethod
    def styled_text(input: str = "", color: str = "white", disabled: bool = False) -> Text:
        if disabled or input == "":
            return None

        text = Text(input)
        text.stylize(color, 0, len(input))
        return text

    @staticmethod
    def styled_label_text(label: str = "", label_color: str = "white", input: str = "", input_color: str = "cyan", disabled: bool = False) -> Text:
        if disabled or input == "":
            return None

        label_text_msg = f"{label}: {input}"

        text = Text(label_text_msg)
        text.stylize(label_color, 0, len(label))
        text.stylize(input_color, len(label) + 1, len(label_text_msg))
        return text

    @staticmethod
    def margin_text(
        margin_text: str = "",
        last_action: str = "WAIT",
    ) -> Text:
        if margin_text == "" or last_action != "BUY":
            return None

        margin_msg = f"Margin: {margin_text}"
        text = Text(margin_msg)

        if margin_text == "0%":
            text.stylize("white", 0, len(margin_msg))
        elif margin_text.startswith("-"):
            text.stylize("white", 0, 5)
            text.stylize("red", 7, len(margin_msg))
        else:
            text.stylize("white", 0, 5)
            text.stylize("green", 7, len(margin_msg))

        return text

    @staticmethod
    def delta_text(
        price: float = 0.0,
        last_buy_price: float = 0.0,
        precision: int = 2,
        last_action: str = "WAIT",
    ) -> Text:
        if price == 0.0 or last_buy_price == 0.0 or last_action != "BUY":
            return None

        delta_msg = f"Delta: {str(round(price - last_buy_price, precision))}"
        text = Text(delta_msg)

        if delta_msg.startswith("Delta: -"):
            text.stylize("white", 0, 5)
            text.stylize("red", 7, len(delta_msg))
        else:
            text.stylize("white", 0, 5)
            text.stylize("green", 7, len(delta_msg))

        return text

    @staticmethod
    def bull_bear(golden_cross: bool = False, adjust_total_periods: int = 300) -> Text:
        if adjust_total_periods < 200:
            return None

        if golden_cross:
            text = Text("BULL")
            text.stylize("green", 0, 4)
        else:
            text = Text("BEAR")
            text.stylize("red", 0, 4)
        return text

    @staticmethod
    def elder_ray(elder_ray_buy: bool = False, elder_ray_sell: bool = False, disabled: bool = False) -> Text:
        if disabled:
            return None

        if elder_ray_buy:
            text = Text("Elder-Ray: buy")
            text.stylize("white", 0, 10)
            text.stylize("green", 11, 14)
        elif elder_ray_sell:
            text = Text("Elder-Ray: sell")
            text.stylize("white", 0, 10)
            text.stylize("red", 11, 15)
        else:
            return None

        return text

    @staticmethod
    def on_balance_volume(obv: float = 0.0, obv_pc: int = 0, disabled: bool = False) -> Text:
        if disabled:
            return None

        obv_msg = f"OBV: {obv:.2f} ({obv_pc}%)"

        if obv >= 0:
            text = Text(obv_msg)
            text.stylize("white", 0, 4)
            text.stylize("green", 5, len(obv_msg))
        else:
            text = Text(f"OBV: {obv:.2f} ({obv_pc}%)")
            text.stylize("white", 0, 4)
            text.stylize("red", 5, len(obv_msg))

        return text

    @staticmethod
    def number_comparison(label: str = "", value1: float = 0.0, value2: float = 0.0, highlight: bool = False, disabled: bool = False) -> Text:
        if disabled:
            return None

        color = "white"
        operator = "="
        if value1 > value2:
            if highlight:
                color = "white on green"
            else:
                color = "green"
            operator = ">"
        elif value1 < value2:
            if highlight:
                color = "white on red"
            else:
                color = "red"
            operator = "<"

        text = Text(f"{label} {value1} {operator} {value2}")
        text.stylize("white", 0, len(label))
        text.stylize(color, len(label) + 1, len(text))
        return text
