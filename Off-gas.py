import streamlit as st
import math

st.set_page_config(
    page_title="EAF Off-Gas Energy Recovery Estimator",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 EAF Off-Gas Energy Recovery Estimator")
st.caption(
    "Enter operating assumptions to estimate recoverable thermal power, energy per heat/day, "
    "steam potential, electricity potential, and CO₂ avoided (based on electricity displacement)."
)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def fmt(x: float, unit: str, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return f"— {unit}"
    return f"{x:.{digits}f} {unit}"

def warn_if(condition: bool, msg: str):
    if condition:
        st.warning(msg)


with st.sidebar:
    st.header("Inputs")

    st.subheader("Gas flow input mode")
    flow_mode = st.selectbox(
        "Choose mode",
        ["Mass flow (kg/s)", "Volumetric flow at N conditions (Nm³/h)"],
        index=0,
    )

    if flow_mode == "Mass flow (kg/s)":
        m_dot = st.number_input("Gas mass flow ṁ (kg/s)", min_value=0.0, value=10.0, step=0.5)
        rho_n = None
        Vn = None
    else:
        Vn = st.number_input("Gas flow V̇N (Nm³/h)", min_value=0.0, value=50000.0, step=1000.0)
        rho_n = st.number_input("Density at N conditions ρN (kg/Nm³)", min_value=0.1, value=1.25, step=0.05)
        m_dot = (Vn * rho_n) / 3600.0  # kg/s

    st.subheader("Thermal conditions")
    Tin = st.number_input("Off-gas inlet temperature Tin (°C)", value=1200.0, step=10.0)
    Tout = st.number_input("Off-gas outlet temperature Tout (°C)", value=250.0, step=10.0)

    st.subheader("Gas property")
    cp = st.number_input("Gas specific heat cp (kJ/kg·K)", min_value=0.1, value=1.10, step=0.05)

    st.subheader("Heat recovery realism")
    eta_hx = st.slider("Heat recovery efficiency ηHX", min_value=0.0, max_value=1.0, value=0.60, step=0.01)

    st.subheader("Time basis")
    time_basis = st.radio(
        "Choose how to compute totals",
        ["Per heat (minutes)", "Per day (hours/day)", "Per day (heats/day)"],
        index=0,
    )
    heat_minutes = None
    hours_per_day = None
    heats_per_day = None

    if time_basis == "Per heat (minutes)":
        heat_minutes = st.number_input("Heat duration (minutes)", min_value=0.0, value=45.0, step=1.0)
    elif time_basis == "Per day (hours/day)":
        hours_per_day = st.number_input("Operating hours/day", min_value=0.0, max_value=24.0, value=16.0, step=0.5)
    else:
        heats_per_day = st.number_input("Heats per day", min_value=0.0, value=20.0, step=1.0)
        heat_minutes = st.number_input("Avg heat duration (minutes)", min_value=0.0, value=45.0, step=1.0)

    st.divider()
    st.header("Optional modules")

    include_steam = st.toggle("Include Steam", value=True)
    include_power = st.toggle("Include Electricity", value=True)
    include_co2 = st.toggle("Include CO₂", value=True)

    
    steam_mode = None
    dh_kj_per_kg = None
    if include_steam:
        st.subheader("Steam settings")
        steam_mode = st.selectbox(
            "Steam enthalpy rise Δh (preset or custom)",
            ["Preset: Low pressure", "Preset: Medium pressure", "Preset: High pressure", "Custom (enter Δh)"],
            index=1,
        )

        presets = {
            "Preset: Low pressure": 2100.0,    # kJ/kg (feedwater -> LP steam, approx)
            "Preset: Medium pressure": 2300.0, # kJ/kg
            "Preset: High pressure": 2600.0,   # kJ/kg
        }
        if steam_mode.startswith("Preset"):
            dh_kj_per_kg = presets[steam_mode]
            st.caption(f"Using Δh ≈ {dh_kj_per_kg:.0f} kJ/kg. Choose Custom to override.")
        else:
            dh_kj_per_kg = st.number_input("Enter Δh (kJ/kg)", min_value=500.0, value=2300.0, step=50.0)

    eta_cycle = 0.15
    if include_power or include_co2:
        st.subheader("Power cycle settings")
        eta_cycle = st.slider("Power cycle efficiency ηcycle", 0.0, 0.50, 0.15, 0.01)
        st.caption("Typical small steam/ORC systems often fall roughly in the ~0.08–0.20 range, depending on conditions.")

    ef_grid = None
    if include_co2:
        st.subheader("CO₂ settings")
        ef_grid = st.number_input(
            "Grid emission factor EFgrid (kg CO₂ / kWh)",
            min_value=0.0,
            value=0.35,
            step=0.01,
            help="CO₂ avoided is estimated by displacing grid electricity with recovered electricity.",
        )

delta_T = Tin - Tout
warn_if(delta_T <= 0, "Tout ≥ Tin → temperature drop is zero/negative. Set Tout lower than Tin to recover heat.")

Q_sens_kW = m_dot * cp * max(delta_T, 0.0)
Q_rec_kW = Q_sens_kW * eta_hx

MWth = Q_rec_kW / 1000.0


E_th_heat_kWh = None
E_th_day_kWh = None

if time_basis == "Per heat (minutes)":
    E_th_heat_kWh = Q_rec_kW * (heat_minutes / 60.0) if heat_minutes is not None else 0.0
elif time_basis == "Per day (hours/day)":
    E_th_day_kWh = Q_rec_kW * hours_per_day if hours_per_day is not None else 0.0
else:
    
    E_th_heat_kWh = Q_rec_kW * (heat_minutes / 60.0) if heat_minutes is not None else 0.0
    E_th_day_kWh = E_th_heat_kWh * heats_per_day if heats_per_day is not None else 0.0


steam_tph = None
if include_steam and dh_kj_per_kg and dh_kj_per_kg > 0:
    msteam_kg_s = Q_rec_kW / dh_kj_per_kg  # (kJ/s) / (kJ/kg) = kg/s
    steam_tph = msteam_kg_s * 3600.0 / 1000.0  # t/h


Pel_kW = None
E_el_heat_kWh = None
E_el_day_kWh = None
if (include_power or include_co2) and eta_cycle is not None:
    Pel_kW = Q_rec_kW * eta_cycle
    
    if time_basis == "Per heat (minutes)":
        E_el_heat_kWh = Pel_kW * (heat_minutes / 60.0) if heat_minutes is not None else 0.0
    elif time_basis == "Per day (hours/day)":
        E_el_day_kWh = Pel_kW * hours_per_day if hours_per_day is not None else 0.0
    else:
        E_el_heat_kWh = Pel_kW * (heat_minutes / 60.0) if heat_minutes is not None else 0.0
        E_el_day_kWh = E_el_heat_kWh * heats_per_day if heats_per_day is not None else 0.0


CO2_heat_t = None
CO2_day_t = None
CO2_year_t = None
if include_co2 and ef_grid is not None:
    
    if E_el_day_kWh is not None:
        CO2_day_kg = E_el_day_kWh * ef_grid
        CO2_day_t = CO2_day_kg / 1000.0
        CO2_year_t = CO2_day_t * 365.0
    if E_el_heat_kWh is not None:
        CO2_heat_kg = E_el_heat_kWh * ef_grid
        CO2_heat_t = CO2_heat_kg / 1000.0


colA, colB = st.columns([1.25, 1])

with colA:
    st.subheader("Results")

    r1, r2, r3, r4, r5 = st.columns(5)

    r1.metric("Recoverable heat", fmt(MWth, "MWth", 3))
    
    if E_th_heat_kWh is not None:
        r2.metric("Recovered energy", fmt(E_th_heat_kWh / 1000.0, "MWh/heat", 3))
    else:
        r2.metric("Recovered energy", fmt(E_th_day_kWh / 1000.0 if E_th_day_kWh is not None else 0.0, "MWh/day", 3))

    if include_steam:
        r3.metric("Steam potential", fmt(steam_tph if steam_tph is not None else 0.0, "t/h", 3))
    else:
        r3.metric("Steam potential", "OFF")

    if include_power:
        r4.metric("Electric power", fmt(Pel_kW / 1000.0 if Pel_kW is not None else 0.0, "MWe", 3))
    else:
        r4.metric("Electric power", "OFF")

    if include_co2:
       
        if CO2_day_t is not None:
            r5.metric("CO₂ avoided", fmt(CO2_day_t, "t/day", 3))
        elif CO2_heat_t is not None:
            r5.metric("CO₂ avoided", fmt(CO2_heat_t, "t/heat", 3))
        else:
            r5.metric("CO₂ avoided", fmt(0.0, "t", 3))
    else:
        r5.metric("CO₂ avoided", "OFF")

    st.divider()

    st.subheader("Breakdown")
    
    rows = []
    rows.append(("Gas mass flow ṁ", fmt(m_dot, "kg/s", 3)))
    rows.append(("ΔT = Tin − Tout", fmt(delta_T, "K", 1)))
    rows.append(("Sensible heat available Q̇sens", fmt(Q_sens_kW / 1000.0, "MW", 3)))
    rows.append(("Recoverable heat Q̇rec", fmt(Q_rec_kW / 1000.0, "MWth", 3)))

    if E_th_heat_kWh is not None:
        rows.append(("Recovered thermal energy per heat", fmt(E_th_heat_kWh / 1000.0, "MWh/heat", 3)))
    if E_th_day_kWh is not None:
        rows.append(("Recovered thermal energy per day", fmt(E_th_day_kWh / 1000.0, "MWh/day", 3)))

    if include_steam:
        rows.append(("Steam enthalpy rise Δh", fmt(dh_kj_per_kg, "kJ/kg", 0)))
        rows.append(("Steam generation", fmt(steam_tph if steam_tph else 0.0, "t/h", 3)))

    if include_power or include_co2:
        rows.append(("Power cycle efficiency ηcycle", fmt(eta_cycle, "-", 2)))
        rows.append(("Electric power", fmt(Pel_kW if Pel_kW else 0.0, "kW", 1)))
        if E_el_heat_kWh is not None:
            rows.append(("Electric energy per heat", fmt(E_el_heat_kWh / 1000.0, "MWh/heat", 3)))
        if E_el_day_kWh is not None:
            rows.append(("Electric energy per day", fmt(E_el_day_kWh / 1000.0, "MWh/day", 3)))

    if include_co2:
        rows.append(("Grid emission factor EFgrid", fmt(ef_grid, "kgCO₂/kWh", 3)))
        if CO2_heat_t is not None:
            rows.append(("CO₂ avoided per heat", fmt(CO2_heat_t, "tCO₂/heat", 3)))
        if CO2_day_t is not None:
            rows.append(("CO₂ avoided per day", fmt(CO2_day_t, "tCO₂/day", 3)))
        if CO2_year_t is not None:
            rows.append(("CO₂ avoided per year", fmt(CO2_year_t, "tCO₂/year", 1)))

    st.table(rows)

with colB:
    st.subheader("Assumptions & sanity checks")

    st.markdown(
        """
**What this model is doing**
- Treats recovery as **sensible heat** from cooling the off-gas: `ṁ · cp · (Tin − Tout)`
- Applies a **single recovery efficiency** `ηHX` to represent real-world losses (fouling, bypass, approach temperatures, etc.)
- Optional modules:
  - **Steam**: converts thermal power into steam flow using `Δh`
  - **Electricity**: converts thermal power into electric power using `ηcycle`
  - **CO₂**: offsets grid electricity using `EFgrid`

**Good practice**
- Use realistic `Tout` (set by your heat exchanger / boiler design constraints).
- Keep `ηHX` conservative unless you have design data.
- For CO₂: enter a grid factor consistent with the scenario you want to compare against.
        """
       
    )

    warn_if(cp < 0.7 or cp > 1.6, "cp looks unusual. Typical hot-gas cp values are often around ~1.0–1.3 kJ/kg·K.")
    warn_if(eta_hx > 0.85, "ηHX > 0.85 is optimistic for many real systems. Make sure you have justification.")
    warn_if(Tin > 2000, "Tin seems very high. Check units/assumptions.")
    warn_if(Tout < 0, "Tout below 0°C is unlikely. Check inputs.")

    st.divider()
    st.subheader("Quick sensitivity (optional)")
    st.caption("This shows how recoverable MWth changes with Tout while keeping other inputs fixed.")

   
    tout_min = min(Tout, Tin - 1.0) if Tin > 1 else 0.0
    tout_max = Tin - 1.0 if Tin > 1 else Tout
    if Tin - 1.0 > 0 and tout_min < tout_max:
        tout_test = st.slider("Sweep Tout (°C)", min_value=float(max(0.0, tout_min)), max_value=float(tout_max), value=float(Tout))
        deltaT_test = max(Tin - tout_test, 0.0)
        Qrec_test_kW = m_dot * cp * deltaT_test * eta_hx
        st.metric("Recoverable heat at swept Tout", fmt(Qrec_test_kW / 1000.0, "MWth", 3))
    else:
        st.info("Set Tin > Tout to enable sensitivity check.")