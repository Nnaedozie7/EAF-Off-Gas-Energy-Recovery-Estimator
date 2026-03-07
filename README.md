# EAF Off-Gas Energy Recovery Estimator

## Overview

Electric Arc Furnaces (EAF) generate large volumes of high temperature off-gas during steelmaking. This gas contains significant thermal energy that is often lost to the environment. Recovering this energy can improve plant efficiency, reduce operating costs, and decrease CO₂ emissions.

This application estimates the **recoverable thermal energy contained in EAF off-gas streams** and evaluates its potential for:

- Heat recovery
- Steam generation
- Electricity production
- CO₂ emission reduction

The tool is implemented using **Python and Streamlit**, providing an interactive interface for evaluating waste heat recovery opportunities in EAF steel plants.

---

## Problem Description

During EAF steelmaking, several reactions generate hot off-gas:

- oxidation of carbon
- oxidation of iron
- combustion of injected fuels
- melting of scrap

Off-gas temperatures can exceed **1000–1500°C**, meaning the gas carries substantial **sensible heat energy**.

Without recovery systems, this energy is typically lost through the exhaust system. Modern steel plants increasingly install **waste heat recovery systems** such as waste heat boilers to capture this energy.

This tool provides a **first-order estimation of the recoverable energy from EAF off-gas**.

---

## Metallurgical Background

Off-gas generation occurs due to reactions such as:

C + O₂ → CO₂  

Fe + O → FeO  

These reactions release heat and produce high-temperature gases.

Typical EAF off-gas characteristics:

| Parameter | Typical Range |
|--------|--------|
| Temperature | 1000 – 1500 °C |
| Flow rate | 10 – 50 kg/s |
| Heat capacity | 1.0 – 1.2 kJ/kg·K |

The thermal energy contained in this gas stream can be recovered through:

- heat exchangers
- waste heat boilers
- steam turbines
- Organic Rankine Cycle (ORC) systems

---

## Methodology

The application estimates recoverable heat using the **sensible heat equation**:

Q = m · Cp · (Tin − Tout)

Where:

- Q = heat recovered (kW)
- m = gas mass flow rate (kg/s)
- Cp = gas heat capacity (kJ/kg·K)
- Tin = gas temperature leaving the furnace
- Tout = temperature after heat recovery

Optional modules estimate:

### Steam Generation

Steam production is estimated using:

m_steam = Q / Δh

Where Δh is the enthalpy change required to convert water to steam.

### Electricity Generation

Electric power generation is estimated using:

P_electric = Q × η

Where η is the efficiency of the power generation system.

### CO₂ Reduction

Electricity generated from recovered heat offsets grid electricity consumption, reducing CO₂ emissions.

---

## Results

The application estimates:

- Recoverable heat from off-gas (MWth)
- Energy recovered per heat (MWh)
- Potential steam generation capacity
- Potential electricity generation
- Estimated CO₂ emissions reduction

These results help engineers evaluate the **energy recovery potential of EAF off-gas systems**.

---

## Code Structure

The application is implemented using **Streamlit**.

Main components include:

1. User input interface for thermodynamic parameters
2. Heat recovery calculation module
3. Optional modules for steam generation and electricity production
4. Result visualization and summary output

---

## How to Run

Install dependencies:

```bash
pip install streamlit
