import streamlit as st
import pandas as pd
import os

# Set the page layout to wide
st.set_page_config(layout="wide")

# Function to load data from the selected Excel file
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    data = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, usecols="B:D", skiprows=6)
        if df.shape[1] == 3:  # Check if there are exactly 3 columns
            df.columns = ['Date', 'Source', 'News']
            df['Stock'] = sheet_name
            df = df.dropna(how='all')
            if not df.empty:  # Check if the DataFrame is not empty
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert Date column to datetime
                df = df.dropna(subset=['Date'])  # Drop rows where 'Date' is NaT
                df['Date'] = df['Date'].dt.strftime('%Y/%m/%d')  # Format Date column as yyyy/mm/dd
                df = df[['Date', 'Stock', 'News', 'Source']]  # Reorder columns
                data[sheet_name] = df
            else:
                st.warning(f"Sheet {sheet_name} is empty and has been skipped.")
        else:
            st.error(f"Sheet {sheet_name} does not have the expected format.")
    if data:
        return pd.concat(data.values(), ignore_index=True)
    else:
        return pd.DataFrame(columns=['Date', 'Stock', 'News', 'Source'])

# Function to consolidate data without duplication
def consolidate_data(new_data, existing_data):
    combined_data = pd.concat([existing_data, new_data]).drop_duplicates().reset_index(drop=True)
    return combined_data

# Function to filter data based on sidebar inputs
def filter_data(df, selected_stocks, start_date, end_date):
    if selected_stocks:
        df = df[df['Stock'].isin(selected_stocks)]
    if start_date and end_date:
        df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
    return df

# Streamlit App
st.title("Stock News Data Viewer")

# Sidebar for user inputs
st.sidebar.header("Options")
action = st.sidebar.selectbox("Choose an action", ("View Fundamental Data", "Browse / Load xlsx file", "Consolidate Data" ))

if action == "View Fundamental Data":
    if os.path.exists("fundamental.csv"):
        df = pd.read_csv("fundamental.csv", parse_dates=['Date']).sort_values(by='Date', ascending=False)
        stocks = sorted(df['Stock'].unique())
        
        selected_stocks = st.sidebar.multiselect("Select Stock(s)", stocks)
        
        if 'start_date' not in st.session_state:
            st.session_state.start_date = df['Date'].min().date()
        if 'end_date' not in st.session_state:
            st.session_state.end_date = df['Date'].max().date()
        
        start_date = st.sidebar.date_input("Start Date", min_value=df['Date'].min().date(), max_value=df['Date'].max().date(), value=st.session_state.start_date)
        end_date = st.sidebar.date_input("End Date", min_value=df['Date'].min().date(), max_value=df['Date'].max().date(), value=st.session_state.end_date)
        
        # Update session state with date input values
        st.session_state.start_date = start_date
        st.session_state.end_date = end_date
        
        if st.sidebar.button("Process Filters"):
            filtered_df = filter_data(df, selected_stocks, st.session_state.start_date, st.session_state.end_date)
            st.header(f"Filtered Data for Selected Stocks")
            st.dataframe(filtered_df)
    else:
        st.warning("No fundamental data available. Please retrieve or load data first.")

elif action == "Retrieve Fundamental Data":
    if st.sidebar.button("Retrieve Dataset"):
        if os.path.exists("fundamental.csv"):
            df = pd.read_csv("fundamental.csv", parse_dates=['Date'])
            st.session_state['data'] = df
            st.success("Data retrieved from fundamental.csv")
        else:
            st.error("fundamental.csv does not exist. Please process a raw file first.")

elif action == "Browse / Load xlsx file":
    file_path = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
    if file_path and st.sidebar.button("Load Data"):
        df = load_data(file_path)
        st.session_state['new_data'] = df
        st.success("Data loaded from file.")

elif action == "Consolidate Data":
    if 'new_data' in st.session_state:
        if os.path.exists("fundamental.csv"):
            existing_df = pd.read_csv("fundamental.csv", parse_dates=['Date'])
            consolidated_df = consolidate_data(st.session_state['new_data'], existing_df)
            consolidated_df.to_csv("fundamental.csv", index=False)
            st.success("Data consolidated and saved to fundamental.csv")
        else:
            st.session_state['new_data'].to_csv("fundamental.csv", index=False)
            st.success("Data saved to fundamental.csv")
    else:
        st.warning("Please load new data first.")



# Ensure data is preserved across interactions
if 'data' in st.session_state:
    df = st.session_state['data']
else:
    df = pd.DataFrame(columns=['Date', 'Stock', 'News', 'Source'])
