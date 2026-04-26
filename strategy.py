class MirrorStrategy:
    def __init__(self, base_buying_power: float, max_alloc: float = 0.05):
        self.buying_power = base_buying_power
        self.max_alloc = max_alloc

    def calculate_notional(self, amount_str: str) -> float:
        """Calculate midpoint of the reported STOCK Act dollar range."""
        try:
            clean = amount_str.replace('$', '').replace(',', '').replace(' ', '')
            if '-' in clean:
                parts = clean.split('-')
                v_min = float(parts[0])
                v_max = float(parts[1])  # was parts[3] — bug fix
                midpoint = (v_min + v_max) / 2
            else:
                midpoint = float(clean.replace('+', ''))

            target_amt = self.buying_power * self.max_alloc
            return round(min(target_amt, midpoint), 2)
        except Exception:
            return 0.0
