# AdipoDelivers Premium Bursary Impact TV

This adds a dedicated **Education Support / Bursary Impact** experience using verified ward-level aggregates only.

## What appears on TV

When at least one ward record is both **Verified** and **Show on TV**, two premium slides are inserted after the opening slide:

1. **Investing in Karachuonyo's Future**
   - total students supported
   - verified bursary allocation
   - wards reached
   - Secondary / College-TVT / University totals

2. **Ward-by-Ward Bursary Reach**
   - proportional horizontal bars
   - ward
   - students supported
   - allocation
   - reporting period

No figures are seeded or invented. If there are no verified figures, the bursary slides do not appear.

## Install

Copy the package contents into the repository root, then run:

```bash
python install_bursary_impact.py
python manage.py migrate
python manage.py check
```

Then open `/control/bursaries/`.

## Privacy

This feature intentionally stores aggregate counts only. Do not enter student names, admission numbers, national IDs, phone numbers, fee balances or other personal student records.
