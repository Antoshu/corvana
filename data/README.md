# Data pack

All data is as of close of business **2026-10-27**. Treat that as "today" for the scenario.
Files in `updates/2026-10-28/` arrived the following morning.

## positions/

| Column | Meaning |
|---|---|
| book | Trading book that holds the position |
| instrument_ref | Identifier as recorded by the order management system |
| ref_type | Which kind of identifier `instrument_ref` is: ISIN, INTERNAL (security master ID) or TICKER |
| quantity | Signed face value (bonds) or notional (derivatives), in `notional_ccy`. Negative means short. |
| notional_ccy | Currency of `quantity` |
| as_of_date | Position date |

Sign conventions for derivatives follow the order management system and are not documented further. State any
assumptions you make.

## Other files

Column names in the other files are intended to be self-explanatory. `sources.yaml` describes the system behind each
file and how far its owner trusts it.
