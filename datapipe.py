import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import os
import time

# --- Configuration ---
PREDICTION_URL = "http://127.0.0.1:5000/predict"
HISTORY_POINTS_REQUIRED = 49  
CURRENT_YEAR = 2025
HISTORIC_CSV_NAME = "clean3.csv"

# --- Blynk API & Conversion Constants ---
# Blynk URL provided by user
BLYNK_URL = "https://blynk.cloud/external/api/getAll?token=tEueg4kzgsG7-RWTIhQF2FpeTrp5ORKE"

# Conversion Factors (approximate standard temperature/pressure values for 20 deg C)
# CO (M=28.01 g/mol): ppm to mg/m^3 (factor ~ 1.145)
CO_CONVERSION_FACTOR = 1.145 
# C6H6 (M=78.11 g/mol): ppb to ug/m^3 (factor ~ 3.195)
C6H6_CONVERSION_FACTOR = 3.195

# The exact 27 features your model expects
FEATURE_COLS = [
    'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
    'CO_lag_1hr', 'CO_lag_24hr', 'C6H6_lag_1hr', 'C6H6_lag_24hr',
    'CO_roll_mean_3hr', 'C6H6_roll_mean_3hr',
    'CO_roll_mean_24hr', 'CO_roll_std_24hr', 'CO_roll_max_24hr',
    'C6H6_roll_mean_24hr', 'C6H6_roll_std_24hr', 'C6H6_roll_max_24hr',
    'CO_diff_1hr', 'CO_diff_24hr', 'C6H6_diff_1hr', 'C6H6_diff_24hr',
    'C6H6_diff_x_hour_sin', 'C6H6_diff_x_hour_cos',
    'CO_diff_x_hour_sin', 'CO_diff_x_hour_cos',
    'is_daytime', 'is_morning_rush', 'is_evening_rush'
]

# -------------------------------------------------------------
# CORE DATA FETCHING FUNCTION
# -------------------------------------------------------------

def fetch_and_average_data(blynk_url, fetch_duration_seconds=60, sleep_time_seconds=1):
    """Fetches data from Blynk API for a duration and returns averaged, converted values."""
    print(f"--- Fetching data from Blynk API for {fetch_duration_seconds} seconds... ---")
    co_readings = []
    c6h6_readings = []
    
    start_time = time.time()
    
    while (time.time() - start_time) < fetch_duration_seconds:
        try:
            response = requests.get(blynk_url)
            response.raise_for_status() # Raise exception for bad status codes
            data = response.json()
            
            # v0 is CO (ppm), v1 is C6H6 (ppb)
            if 'v0' in data and 'v1' in data:
                co_readings.append(float(data.get('v0')))
                c6h6_readings.append(float(data.get('v1')))
            
        except requests.exceptions.RequestException as e:
            print(f"Blynk API Error during fetch: {e}")
        except json.JSONDecodeError:
            print("Blynk API Error: Could not decode JSON response.")
        
        time.sleep(sleep_time_seconds)
        
    if len(co_readings) < 10: # Require a minimum number of successful reads
        raise ValueError(f"Failed to retrieve sufficient data from Blynk API. Only {len(co_readings)} successful fetches.")
        
    # Calculate averages (in original units)
    avg_co_ppm = np.mean(co_readings)
    avg_c6h6_ppb = np.mean(c6h6_readings)
    
    # Convert to model units
    new_raw_co_mgm3 = avg_co_ppm * CO_CONVERSION_FACTOR
    new_raw_c6h6_ugm3 = avg_c6h6_ppb * C6H6_CONVERSION_FACTOR
    
    print(f"✅ Fetch complete. Avg CO: {avg_co_ppm:.2f} ppm -> {new_raw_co_mgm3:.4f} mg/m^3")
    print(f"✅ Avg C6H6: {avg_c6h6_ppb:.2f} ppb -> {new_raw_c6h6_ugm3:.4f} ug/m^3")
    
    return new_raw_co_mgm3, new_raw_c6h6_ugm3

# -------------------------------------------------------------
# HISTORY SYNTHESIS AND PIPELINE EXECUTION (Modified only in run_automation)
# -------------------------------------------------------------

def load_and_synthesize_history(current_dt: datetime) -> pd.DataFrame:
    """
    Loads data from clean3.csv, finds the matching historical period (Month/Day),
    and synthesizes a new DataFrame with the current year (2025).
    """
    print("\n--- 1. Synthesizing Historical Data ---")
    try:
        df = pd.read_csv(HISTORIC_CSV_NAME)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: '{HISTORIC_CSV_NAME}' not found.")

    df['DateTime_Original'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour']])
    df.sort_values('DateTime_Original', inplace=True)
    
    target_dates = set()
    for i in range(4): 
        dt = current_dt - timedelta(days=i)
        target_dates.add((dt.month, dt.day))
    
    historic_slice = df[
        df.apply(lambda row: (row['Month'], row['Day']) in target_dates, axis=1)
    ].copy()

    if historic_slice.empty:
        raise ValueError(f"No historical data found matching Month/Day combinations for the past 4 days: {target_dates}")

    historic_slice['Year'] = CURRENT_YEAR
    historic_slice['DateTime_Synth'] = pd.to_datetime(historic_slice[['Year', 'Month', 'Day', 'Hour']])
    
    historic_slice.sort_values('DateTime_Synth', inplace=True)

    T_minus_1_dt = current_dt - timedelta(hours=1)
    final_history = historic_slice[historic_slice['DateTime_Synth'] <= T_minus_1_dt].copy()

    final_history = final_history.tail(HISTORY_POINTS_REQUIRED).reset_index(drop=True)
    
    if len(final_history) < HISTORY_POINTS_REQUIRED:
        print(f"⚠️ Warning: Found only {len(final_history)} historical points. Missing data for full 48hr display/T-25 point.")
        
    print(f"✅ Synthesized history has {len(final_history)} points (T-{len(final_history)} to T-1) ready.")
    
    return final_history


def run_automation():
    
    # T = Current time rounded down to the hour
    current_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    # --- STEP 1: Fetch and Convert Live Data ---
    try:
        new_raw_co, new_raw_c6h6 = fetch_and_average_data(BLYNK_URL)
    except ValueError as e:
        print(f"❌ Aborting prediction due to data retrieval error: {e}")
        return
    except Exception as e:
        print(f"❌ Aborting prediction due to unexpected error: {e}")
        return
        
    # 2. Synthesize History (for T-25 to T-1)
    try:
        df_history = load_and_synthesize_history(current_dt)
    except Exception as e:
        print(f"\n❌ FATAL HISTORY ERROR: {e}")
        return
    
    # --- DEBUG 1: Display Synthesized Raw Data (Last 48 hours) ---
    print("\n" + "="*80)
    print(f"DEBUG 1: SYNTHESIZED RAW DATA (Year {CURRENT_YEAR}) - Last 48 Hours (T-48 to T-1)")
    print("="*80)
    
    display_df = df_history.tail(48).copy() 
    print(display_df[['DateTime_Synth', 'Hour', 'CO(GT)', 'C6H6(GT)']])
    print("="*80)
    
    # --- 3. Append New Data to History ---
    new_data = {
        'Year': current_dt.year, 'Month': current_dt.month, 'Day': current_dt.day, 'Hour': current_dt.hour,
        # Use converted values here:
        'CO(GT)': new_raw_co, 'C6H6(GT)': new_raw_c6h6, 'DateTime_Synth': current_dt 
    }
    
    df_new_row = pd.DataFrame([new_data])
    columns_for_fe = ['Year', 'Month', 'Day', 'Hour', 'CO(GT)', 'C6H6(GT)', 'DateTime_Synth']
    df_history_clean = df_history[[col for col in df_history.columns if col in columns_for_fe]]

    df_combined = pd.concat([df_history_clean, df_new_row], ignore_index=True)
    
    # --- 4. Automate Feature Engineering ---
    df = df_combined.copy()
    
    numeric_cols = ['Hour', 'CO(GT)', 'C6H6(GT)']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce') 
    
    # Feature Calculation Logic
    df['day_of_week_num'] = df['DateTime_Synth'].dt.dayofweek
    df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24.0)
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week_num'] / 7.0)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week_num'] / 7.0)
    df['CO_lag_1hr'] = df['CO(GT)'].shift(1)
    df['CO_lag_24hr'] = df['CO(GT)'].shift(24)
    df['C6H6_lag_1hr'] = df['C6H6(GT)'].shift(1)
    df['C6H6_lag_24hr'] = df['C6H6(GT)'].shift(24)
    df['CO_roll_mean_3hr'] = df['CO(GT)'].shift(1).rolling(window=3).mean()
    df['C6H6_roll_mean_3hr'] = df['C6H6(GT)'].shift(1).rolling(window=3).mean()
    df['CO_roll_mean_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).mean()
    df['CO_roll_std_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).std()
    df['CO_roll_max_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).max()
    df['C6H6_roll_mean_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).mean()
    df['C6H6_roll_std_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).std()
    df['C6H6_roll_max_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).max()
    df['CO_diff_1hr'] = df['CO(GT)'].diff(1).shift(1)
    df['CO_diff_24hr'] = df['CO(GT)'].diff(24).shift(1) 
    df['C6H6_diff_1hr'] = df['C6H6(GT)'].diff(1).shift(1)
    df['C6H6_diff_24hr'] = df['C6H6(GT)'].diff(24).shift(1) 
    df['C6H6_diff_x_hour_sin'] = df['C6H6_diff_1hr'] * df['hour_sin']
    df['C6H6_diff_x_hour_cos'] = df['C6H6_diff_1hr'] * df['hour_cos']
    df['CO_diff_x_hour_sin'] = df['CO_diff_1hr'] * df['hour_sin']
    df['CO_diff_x_hour_cos'] = df['CO_diff_1hr'] * df['hour_cos']
    df['is_daytime'] = ((df['Hour'] >= 7) & (df['Hour'] <= 20)).astype(int)
    df['is_morning_rush'] = ((df['Hour'] >= 7) & (df['Hour'] <= 9)).astype(int)
    df['is_evening_rush'] = ((df['Hour'] >= 17) & (df['Hour'] <= 19)).astype(int)

    # 5. Extract the final row (the current hour T)
    latest_features = df.tail(1)[FEATURE_COLS].to_dict('records')[0]
    
    # --- DEBUG 2: Display Engineered Features (T) ---
    print("\n--- DEBUG 2: ENGINEERED FEATURES (T) ---")
    engineered_df = df.tail(1)[FEATURE_COLS].T
    engineered_df.columns = ['Value (T)']
    print(engineered_df)
    print("-" * 40)
    
    # Final check for NaNs
    if any(pd.isna(v) for v in latest_features.values()):
        nan_features = {k: v for k, v in latest_features.items() if pd.isna(v)}
        print("\n❌ CRITICAL WARNING: NaNs still detected in features.")
        print(f"NaN features: {list(nan_features.keys())}")
        print("\nACTION: Check DEBUG 1 output for gaps in the historical data, or if the current time matches a known data sparse period in clean3.csv.")
        return
        
    # --- 6. Send Prediction Request (only runs if no NaNs) ---
    
    print("\n" + "="*50)
    print("Payload successfully generated.")
    print("="*50)

    try:
        print(f"\nSending request to server at {PREDICTION_URL}...")
        response = requests.post(PREDICTION_URL, json=latest_features)
        response.raise_for_status()
        
        prediction = response.json()
        print("\n✅ Prediction Successful:")
        print(f"Predicted for: {(current_dt + timedelta(hours=1)).strftime('%Y-%m-%d %H:00')}")
        print(json.dumps(prediction, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR communicating with the server at {PREDICTION_URL}.")
        print("Please ensure your 'app.py' server is running in a separate terminal.")
        print(f"Details: {e}")
        
if __name__ == '__main__':
    run_automation()