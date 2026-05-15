
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math

def _last_day_of_month(d: date) -> date:
    import calendar
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])

def _compute_schedule(start: date, pv: float, years: int):
    end_date = (start + relativedelta(years=years)) - timedelta(days=1)
    total_days = years * 365
    daily_amount = pv / total_days
    
    rows = []
    cum_estimated = 0.0
    current = start
    while current <= end_date:
        dep_date = _last_day_of_month(current)
        if dep_date > end_date:
            dep_date = end_date
        
        days_in_period = (dep_date - current).days + 1
        base_amount = daily_amount * days_in_period
        
        if dep_date >= end_date:
            base_amount = pv - cum_estimated
            
        base_amount = max(0.0, base_amount)
        cum_estimated += base_amount
        rows.append({
            "date": dep_date,
            "days": days_in_period,
            "amount": base_amount
        })
        current = (dep_date.replace(day=1) + relativedelta(months=1))
    return rows

# Test Case
start_date = date(2025, 3, 15)
pv = 100000.0
years = 5

schedule = _compute_schedule(start_date, pv, years)

print(f"Asset starting {start_date} with PV={pv} over {years} years.")
print("-" * 50)
year_2025 = [r for r in schedule if r["date"].year == 2025]
total_2025 = sum(r["amount"] for r in year_2025)
total_days_2025 = sum(r["days"] for r in year_2025)

print(f"Year 2025 Rows:")
for r in year_2025:
    print(f"  {r['date']} : {r['days']} days -> {r['amount']:.2f}")

print("-" * 50)
print(f"Total for 2025: {total_2025:.2f} over {total_days_2025} days.")

theoretical_daily = pv / (years * 365)
expected = theoretical_daily * total_days_2025
print(f"Theoretical (Daily * 292): {expected:.2f}")
