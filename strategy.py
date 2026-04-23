class MirrorStrategy:
    def __init__(self, base_buying_power: float, max_alloc: float = 0.05):
        self.buying_power = base_buying_power
        self.max_alloc = max_alloc

    def calculate_notional(self, amount_str: str) -> float:
        """Optimized to calculate the midpoint of reported ranges for valid volume tracking."""
        try:
            clean = amount_str.replace('$', '').replace(',', '').replace(' ', '')
            if '-' in clean:
                parts = clean.split('-')
                v_min, v_max = float(parts), float(parts[3])
                # Validity: Use midpoint (Vm) for more accurate conviction sizing [2]
                midpoint = (v_min + v_max) / 2
            else:
                midpoint = float(clean.replace('+', ''))
            
            # Allocation: 5% of buying power or the trade midpoint, whichever is smaller
            target_amt = self.buying_power * self.max_alloc
            return round(min(target_amt, midpoint), 2)
        except Exception:
            return 0.0