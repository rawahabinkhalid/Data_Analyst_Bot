import sqlite3
import pandas as pd

# Function to create a SQLite database and save DataFrame to a specified table
def create_table_from_dataframe(conn, df, table_name):
    df.to_sql(table_name, conn, if_exists='replace', index=False)

# Function to generate a date table with date details
def generate_date_id_mapping(dates):
    unique_dates = pd.DataFrame(dates.unique(), columns=['date'])
    unique_dates['date_id'] = unique_dates.index + 1
    unique_dates['year'] = unique_dates['date'].dt.year
    unique_dates['month'] = unique_dates['date'].dt.month
    unique_dates['day'] = unique_dates['date'].dt.day
    unique_dates['quarter'] = unique_dates['date'].dt.quarter
    unique_dates['day_of_week'] = unique_dates['date'].dt.dayofweek
    unique_dates['day_name'] = unique_dates['date'].dt.day_name()
    return unique_dates

# Main function to import data from Excel sheets into DataFrames and create database tables
def main():
    excel_file = 'US_Regional_Sales_Data.xlsx'  # Provide the path to your Excel file
    sheets = [
        "Customers Sheet",
        "Store Locations Sheet",
        "Products Sheet",
        "Regions Sheet",
        "Sales Team Sheet"
    ]
    
    # Connect to SQLite database (it will create the database if it doesn't exist)
    conn = sqlite3.connect('sales_dataset.db')
    
    # Load each sheet into a DataFrame and save to the database
    for sheet_name in sheets:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        create_table_from_dataframe(conn, df, sheet_name.replace(" ", "_"))

    # Load the Sales Orders Sheet to update date columns
    sales_df = pd.read_excel(excel_file, sheet_name="Sales Orders Sheet")
    
    # Convert date columns to datetime
    date_columns = ['ProcuredDate', 'OrderDate', 'ShipDate', 'DeliveryDate']
    for col in date_columns:
        sales_df[col] = pd.to_datetime(sales_df[col], format='%d/%m/%Y')
    
    # Combine all date columns to find unique dates
    all_dates = pd.concat([sales_df[col] for col in date_columns])

    # Generate date ID mapping
    date_df = generate_date_id_mapping(all_dates)

    # Sort the date table by date and reset the IDs
    date_df = date_df.sort_values(by='date').reset_index(drop=True)
    date_df['date_id'] = date_df.index + 1

    # Replace date columns in sales table with sorted date IDs and rename columns
    for col in date_columns:
        sales_df[col] = sales_df[col].map(date_df.set_index('date')['date_id'])
        sales_df.rename(columns={col: f"{col}ID"}, inplace=True)

    # Save the updated sales table and sorted date table to the database
    create_table_from_dataframe(conn, sales_df, "Sales_Orders_Sheet")
    create_table_from_dataframe(conn, date_df, "Date_Table")

    # Close the connection
    conn.close()
    print("Data imported successfully!")

if __name__ == "__main__":
    main()
