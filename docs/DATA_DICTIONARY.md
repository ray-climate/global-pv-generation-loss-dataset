# Data Dictionary (CSV-only)

## 1) `data/global_pv_facility_inventory.csv`

| Variable | Type | Unit | Description |
|---|---|---|---|
| `PV_ID` | integer | none | Unique facility identifier. |
| `latitude` | float | decimal degrees | Facility reference latitude (WGS84). |
| `longitude` | float | decimal degrees | Facility reference longitude (WGS84). |
| `country` | string | none | Country name associated with the facility. |
| `year` | integer | YYYY | Facility year attribute. |
| `area_m2` | float | m2 | Facility area in square meters. |

## 2) `data/pv_generation_losses/PV_facility_generation_year_YYYY.csv`

| Variable | Type | Unit | Description |
|---|---|---|---|
| `PV_ID` | integer | none | Facility identifier (join key). |
| `latitude` | float | decimal degrees | Facility latitude. |
| `longitude` | float | decimal degrees | Facility longitude. |
| `country` | string | none | Country label. |
| `year` | integer | YYYY | Data year (matches file year). |
| `area_m2` | float | m2 | Facility area. |
| `power_POA (kWh)` | float | kWh | POA generation estimate. |
| `power_POA_clr (kWh)` | float | kWh | Clear-sky reference generation estimate. |
| `power_POA_cln (kWh)` | float | kWh | Clean-atmosphere reference generation estimate. |
| `aerosol_loss (kWh)` | float | kWh | Estimated generation loss attributable to aerosol effects. |
