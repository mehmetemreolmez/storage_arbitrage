import streamlit as st
import pandas as pd

import pulp as pl
import numpy as np
import warnings
warnings.filterwarnings('ignore')

import io


@st.cache_data

def SingleOperation(data,  storage_capacity, max_injection, max_withdrawal,injection_efficiency, withdrawal_efficiency, injection_variable_cost, withdrawal_variable_cost):
    # Define the optimization problem
    model = pl.LpProblem("Maximize_Revenue", pl.LpMaximize)
    # Extract parameters from the DataFrame
    hours = data['Hour'].tolist()
    day_ahead_price = data.set_index('Hour')['Price'].to_dict()
    # Define variables for storage
    stored_in = pl.LpVariable.dicts("Storage_In", hours, lowBound=0)
    stored_out = pl.LpVariable.dicts("Storage_Out", hours, lowBound=0)
    storage_start = pl.LpVariable.dicts("Storage_Start", hours, lowBound=0, upBound=storage_capacity)
    storage_end = pl.LpVariable.dicts("Storage_End", hours, lowBound=0, upBound=storage_capacity)
    # Objective Function
    model += pl.lpSum([day_ahead_price[hour] * stored_out[hour] - day_ahead_price[hour] * stored_in[hour] - stored_in[hour] * withdrawal_variable_cost - stored_out[hour] * injection_variable_cost for hour in hours])
    # Constraints
    for hour in hours:
        if hour == 0:
            model += storage_start[hour] == 0  # Initial storage capacity
        else:
            model += storage_start[hour] == storage_end[hour - 1]

        model += storage_end[hour] == storage_start[hour] + (stored_in[hour] * withdrawal_efficiency) - (stored_out[hour] * injection_efficiency)
        model += stored_in[hour] <= storage_capacity - storage_start[hour]
        model += stored_in[hour] <= max_withdrawal
        model += stored_out[hour] <= storage_start[hour]
        model += stored_out[hour] <=  max_injection
        
        model += storage_end[hour] <= storage_capacity

    # Solve the model
    model.solve()

    # Extracting the results
    data['Storage_In'] = [pl.value(stored_in[hour]) for hour in hours]
    data['Storage_Out'] = [pl.value(stored_out[hour]) for hour in hours]
    data['Storage_Start'] = [pl.value(storage_start[hour]) for hour in hours]
    data['Storage_End'] = [pl.value(storage_end[hour]) for hour in hours]

    total_revenue = pl.value(model.objective)  
    return data, total_revenue


st.title("Arbitraj hesaplama modülü çok yakında hizmetinizde :)")

storage_capacity=st.number_input("Storage Capacity (MWh)")
max_injection=st.number_input("Maximum injection to transmission line in the time interval (MWh)")
max_withdrawal=st.number_input("Maximum withdrawal from the transmission line in the time interval (MWh)")

injection_efficiency=st.number_input("Efficiency in injection to transmission line (if 0,95, it means 1 MWh is used from storage to feed transmission line 0,95 MWh)")
withdrawal_efficiency=st.number_input("Efficiency in withdrawing from transmission line (If 0,9, it means 1 MWh is withdrawn to store 0,9 for storing 1 MWh)")


injection_variable_cost=st.number_input("Variable cost for 1 MW injection to transmission line")
withdrawal_variable_cost=st.number_input("Variable cost for 1 MWh withdraw from the transmission line")

file=st.file_uploader("Choose a file",type=['xlsx'])
if file is not None:
    st.write((f'You have uploaded {file.name}'))
    my_data=pd.read_excel(file,engine='openpyxl')
    
#if st.button("Calculate"):
detay, toplam_gelir = SingleOperation(my_data, storage_capacity, max_injection, max_withdrawal,injection_efficiency, withdrawal_efficiency, injection_variable_cost,withdrawal_variable_cost)
st.write(toplam_gelir)

#if st.button("Download Result in Detail"):
detay.to_excel('results.xlsx')
st.write(detay)
