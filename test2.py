import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import time
import optuna
import matplotlib.pyplot as plt
import seaborn as sns

print("--- Step 1: Load and Prepare Data ---")
try:
    df = pd.read_csv("clean3.csv")
except FileNotFoundError:
    print("Error: 'clean3.csv' not found.")
    exit()

# Create a proper DateTime index and get Day of Week Name
df['DateTime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour']])
df.sort_values('DateTime', inplace=True)
df['Weekday'] = df['DateTime'].dt.day_name()
print("Data loaded and prepared.")


# --- Step 1.5: Create Time Series Features ---
print("--- Step 1.5: Creating Time Series Features ---")
# Lags
df['CO_lag_1hr'] = df['CO(GT)'].shift(1)
df['CO_lag_24hr'] = df['CO(GT)'].shift(24)
df['C6H6_lag_1hr'] = df['C6H6(GT)'].shift(1)
df['C6H6_lag_24hr'] = df['C6H6(GT)'].shift(24)
# Rolling Windows
df['CO_roll_mean_3hr'] = df['CO(GT)'].shift(1).rolling(window=3).mean()
df['C6H6_roll_mean_3hr'] = df['C6H6(GT)'].shift(1).rolling(window=3).mean() # <-- Fixed typo C66->C6H6

# Drop rows with NaNs created by initial shifting/rolling
df = df.dropna()
df.reset_index(drop=True, inplace=True)
print("Lag and rolling features created.")

# Cyclical time features
print("Creating cyclical time features...")
df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24.0)
df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24.0)
df['day_of_week_num'] = df['DateTime'].dt.dayofweek
df['day_sin'] = np.sin(2 * np.pi * df['day_of_week_num'] / 7.0)
df['day_cos'] = np.cos(2 * np.pi * df['day_of_week_num'] / 7.0)
print("Cyclical features created.")

# Advanced rolling and difference features
print("Creating advanced rolling window and difference features...")
df['CO_roll_mean_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).mean()
df['CO_roll_std_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).std()
df['CO_roll_max_24hr'] = df['CO(GT)'].shift(1).rolling(window=24).max()
df['C6H6_roll_mean_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).mean()
df['C6H6_roll_std_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).std()
df['C6H6_roll_max_24hr'] = df['C6H6(GT)'].shift(1).rolling(window=24).max()

# Difference (Momentum) Features
df['CO_diff_1hr'] = df['CO(GT)'].diff(1).shift(1)
df['CO_diff_24hr'] = df['CO(GT)'].diff(24).shift(1)
df['C6H6_diff_1hr'] = df['C6H6(GT)'].diff(1).shift(1)
df['C6H6_diff_24hr'] = df['C6H6(GT)'].diff(24).shift(1)

# Interaction Features
print("Creating interaction features...")
df['C6H6_diff_x_hour_sin'] = df['C6H6_diff_1hr'] * df['hour_sin']
df['C6H6_diff_x_hour_cos'] = df['C6H6_diff_1hr'] * df['hour_cos']
df['CO_diff_x_hour_sin'] = df['CO_diff_1hr'] * df['hour_sin']
df['CO_diff_x_hour_cos'] = df['CO_diff_1hr'] * df['hour_cos']

# 'State' Features
print("Creating 'state' features (daytime, rush hour)...")
df['is_daytime'] = ((df['Hour'] >= 7) & (df['Hour'] <= 20)).astype(int)
print("Creating 'weekend' and 'weekday rush' features...")

# Feature 4: Is it the weekend?
df['is_weekend'] = (df['Weekday'].isin(['Saturday', 'Sunday'])).astype(int)

# Feature 5: Is it a WEEKDAY morning rush?
df['is_weekday_morning_rush'] = ((df['is_weekend'] == 0) & 
                                (df['Hour'] >= 7) & 
                                (df['Hour'] <= 9)).astype(int)

# Feature 6: Is it a WEEKDAY evening rush?
df['is_weekday_evening_rush'] = ((df['is_weekend'] == 0) & 
                                (df['Hour'] >= 17) & 
                                (df['Hour'] <= 19)).astype(int)

# --- CRITICAL: Drop all NaNs from new features ---
df = df.dropna()
df.reset_index(drop=True, inplace=True)
print("All features created and NaNs dropped.")


# --- Step 2: Split Data (Chronologically) ---
print("--- Step 2: Splitting Data ---")
N = len(df)
n_train = int(N * 0.70)
n_val = int(N * 0.15)
n_test = N - n_train - n_val
df_train = df.iloc[:n_train].copy()
df_val = df.iloc[n_train:n_train + n_val].copy()
df_test = df.iloc[n_train + n_val:].copy()
print(f"Train: {len(df_train)}, Val: {len(df_val)}, Test: {len(df_test)}")


# --- Steps 3 & 4 (REMOVED) ---
print("\n--- Steps 3 & 4: Skipped (CatBoost handles categories) ---")


# --- Define Feature List (Used by Optuna and Final Model) ---
features = [
    'hour_sin', 'hour_cos', 
    'day_sin', 'day_cos',
    'CO_lag_1hr', 'CO_lag_24hr',
    'C6H6_lag_1hr', 'C6H6_lag_24hr',
    'CO_roll_mean_3hr', 'C6H6_roll_mean_3hr',
    'CO_roll_mean_24hr', 'CO_roll_std_24hr', 'CO_roll_max_24hr',
    'C6H6_roll_mean_24hr', 'C6H6_roll_std_24hr', 'C6H6_roll_max_24hr',
    'CO_diff_1hr', 'CO_diff_24hr',
    'C6H6_diff_1hr', 'C6H6_diff_24hr',
    'C6H6_diff_x_hour_sin', 'C6H6_diff_x_hour_cos',
    'CO_diff_x_hour_sin', 'CO_diff_x_hour_cos',
    'is_daytime',
    'is_weekend',
    'is_weekday_morning_rush',
    'is_weekday_evening_rush'
]
targets = ['CO(GT)', 'C6H6(GT)']
categorical_features = []

# --- Define Train, Val, Test sets (Used by Optuna and Final Model) ---
X_train = df_train[features]
y_train = df_train[targets]
X_val = df_val[features]
y_val = df_val[targets]
X_test = df_test[features]
y_test = df_test[targets]


# --- Step 5: Optuna Hyperparameter Tuning ---
print("\n--- Step 5: Starting Optuna Hyperparameter Tuning ---")

# Use your last best scores as the new baseline
BASELINE_MAE_CO = 0.3695 
BASELINE_MAE_C6H6 = 1.6308

def objective(trial):
    # 1. Define the hyperparameter search space
    params = {
        'iterations': 1000,
        'early_stopping_rounds': 100,
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'depth': trial.suggest_int('depth', 5, 10),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0, log=True),
        'subsample': trial.suggest_float('subsample', 0.7, 1.0),
        'random_seed': 42,
        'verbose': False
    }

    # --- Train CO Model ---
    model_co = CatBoostRegressor(**params)
    model_co.fit(
        X_train, y_train['CO(GT)'],
        eval_set=(X_val, y_val['CO(GT)']),
        cat_features=categorical_features
    )
    
    # --- Train C6H6 Model ---
    model_c6h6 = CatBoostRegressor(**params)
    model_c6h6.fit(
        X_train, y_train['C6H6(GT)'],
        eval_set=(X_val, y_val['C6H6(GT)']),
        cat_features=categorical_features
    )

    # --- Evaluate on validation data ---
    y_pred_co = model_co.predict(X_val)
    y_pred_c6h6 = model_c6h6.predict(X_val)
    
    mae_co = mean_absolute_error(y_val['CO(GT)'], y_pred_co)
    mae_c6h6 = mean_absolute_error(y_val['C6H6(GT)'], y_pred_c6h6)
    
    # 4. Return a combined, normalized score for Optuna to minimize
    normalized_score = (mae_co / BASELINE_MAE_CO) + (mae_c6h6 / BASELINE_MAE_C6H6)
    
    return normalized_score

# --- Create and run the study ---
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50) # Run 50 trials

print("--- Optuna Tuning Complete ---")
print(f"Best normalized score: {study.best_value:.4f}")
print("Best parameters found:")
print(study.best_params)


# --- Step 6: Train FINAL Models with Best Params ---
print("\n--- Step 6: Training Final Models with Best Parameters ---")

# --- Get the best parameters from the Optuna study ---
best_params = study.best_params

# Set the final, non-tuned parameters
best_params['iterations'] = 3000          # Higher iterations for the slow learning rate
best_params['early_stopping_rounds'] = 200 # More patience
best_params['random_seed'] = 42
best_params['verbose'] = False

# --- Train CO Model ---
print("Training final CO(GT) model...")
start_co = time.time()
model_co = CatBoostRegressor(**best_params) # Use best_params
model_co.fit(
    X_train, y_train['CO(GT)'],
    eval_set=(X_val, y_val['CO(GT)']),
    cat_features=categorical_features
)
end_co = time.time()
print(f"Final CO(GT) training complete in {end_co - start_co:.2f} seconds.")
print(f"Best iteration for CO(GT): {model_co.get_best_iteration()}")


# --- Train C6H6 Model ---
print("Training final C6H6(GT) model...")
start_c6h6 = time.time()
model_c6h6 = CatBoostRegressor(**best_params) # Use best_params
model_c6h6.fit(
    X_train, y_train['C6H6(GT)'],
    eval_set=(X_val, y_val['C6H6(GT)']),
    cat_features=categorical_features
)
end_c6h6 = time.time()
print(f"Final C6H6(GT) training complete in {end_c6h6 - start_c6h6:.2f} seconds.")
print(f"Best iteration for C6H6(GT): {model_c6h6.get_best_iteration()}")

# --- Get Feature Importance from the *final* models ---
print("--- Final CO(GT) Model Feature Importance ---")
co_importance = model_co.get_feature_importance(prettified=True)
print(co_importance.head(10))

print("--- Final C6H6(GT) Model Feature Importance ---")
c6h6_importance = model_c6h6.get_feature_importance(prettified=True)
print(c6h6_importance.head(10))


# --- Step 7: Evaluate Models on TEST Set ---
print("\n--- Step 7: Evaluating Final Models on Test Set ---")

# Predict on the test set
y_pred_co = model_co.predict(X_test)
y_pred_c6h6 = model_c6h6.predict(X_test)

# Combine/stack predictions
y_pred_actual = np.stack([y_pred_co, y_pred_c6h6], axis=1)

# Calculate metrics
r2 = r2_score(y_test, y_pred_actual)
mae_co = mean_absolute_error(y_test['CO(GT)'], y_pred_actual[:, 0])
mae_c6h6 = mean_absolute_error(y_test['C6H6(GT)'], y_pred_actual[:, 1])

print(f"\n--- FINAL CatBoost Performance (TUNED) ---")
print(f"Final R-squared: {r2:.4f}")
print(f"Final Mean Absolute Error for CO(GT): {mae_co:.4f}")
print(f"Final Mean Absolute Error for C6H6(GT): {mae_c6h6:.4f}")


# --- Step 8: Compare Actual vs. Predicted ---
print("\n--- Step 8: Comparing Actual vs. Predicted Values ---")

comparison_df = pd.DataFrame({
    'Actual_CO': y_test['CO(GT)'],
    'Predicted_CO': y_pred_actual[:, 0],
    'Actual_C6H6': y_test['C6H6(GT)'],
    'Predicted_C6H6': y_pred_actual[:, 1]
}, index=y_test.index)

# Add difference columns
comparison_df['Diff_CO'] = comparison_df['Actual_CO'] - comparison_df['Predicted_CO']
comparison_df['Diff_C6H6'] = comparison_df['Actual_C6H6'] - comparison_df['Predicted_C6H6']

print("Showing first 20 rows of the test set comparison:")
print(comparison_df.head(20))


# -----------------------------------------------------------------
# --- Step 9: Error (Residual) Analysis ---
# -----------------------------------------------------------------
print("\n--- Step 9: Starting Error (Residual) Analysis ---")

# 1. Combine the test features with the comparison results
analysis_df = df_test.join(comparison_df)

# 2. Calculate Absolute Errors for sorting
analysis_df['Abs_Diff_CO'] = analysis_df['Diff_CO'].abs()
analysis_df['Abs_Diff_C6H6'] = analysis_df['Diff_C6H6'].abs()

print("--- Analysis DataFrame successfully created ---")

# 3. Find the Top 20 Largest Errors for CO(GT)
print("\n--- Top 20 Largest Errors for CO(GT) (by Absolute Difference) ---")
top_20_errors_co = analysis_df.sort_values(by='Abs_Diff_CO', ascending=False)
print(top_20_errors_co[['DateTime', 'Hour', 'Weekday', 'Actual_CO', 'Predicted_CO', 'Abs_Diff_CO']].head(20))

# 4. Find the Top 20 Largest Errors for C6H6(GT)
print("\n--- Top 20 Largest Errors for C6H6(GT) (by Absolute Difference) ---")
top_20_errors_c6h6 = analysis_df.sort_values(by='Abs_Diff_C6H6', ascending=False)
print(top_20_errors_c6h6[['DateTime', 'Hour', 'Weekday', 'Actual_C6H6', 'Predicted_C6H6', 'Abs_Diff_C6H6']].head(20))


# 5. Group Errors by Hour of Day
print("\n--- Mean Absolute Error by Hour of Day ---")
error_by_hour = analysis_df.groupby('Hour')[['Abs_Diff_CO', 'Abs_Diff_C6H6']].mean()
print(error_by_hour)

# 6. Group Errors by Weekday
print("\n--- Mean Absolute Error by Weekday ---")
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
error_by_weekday = analysis_df.groupby('Weekday')[['Abs_Diff_CO', 'Abs_Diff_C6H6']].mean().reindex(weekday_order)
print(error_by_weekday)

# 7. Plot Residuals
print("\n--- Generating Residual Plots ---")

fig, axes = plt.subplots(3, 2, figsize=(18, 18))
fig.suptitle('Residual Analysis (Actual - Predicted)', fontsize=20, y=1.03)

# Plot 1: Histogram of CO Residuals
sns.histplot(analysis_df['Diff_CO'], kde=True, ax=axes[0, 0], bins=30)
axes[0, 0].set_title('Histogram of CO(GT) Residuals', fontsize=14)
axes[0, 0].set_xlabel('Error (Diff_CO)', fontsize=12)
axes[0, 0].axvline(0, color='red', linestyle='--')

# Plot 2: Histogram of C6H6 Residuals
sns.histplot(analysis_df['Diff_C6H6'], kde=True, ax=axes[0, 1], bins=30)
axes[0, 1].set_title('Histogram of C6H6(GT) Residuals', fontsize=14)
axes[0, 1].set_xlabel('Error (Diff_C6H6)', fontsize=12)
axes[0, 1].axvline(0, color='red', linestyle='--')

# Plot 3: CO Errors by Hour
error_by_hour['Abs_Diff_CO'].plot(kind='bar', ax=axes[1, 0])
axes[1, 0].set_title('Mean Absolute Error (CO) by Hour', fontsize=14)
axes[1, 0].set_xlabel('Hour of Day', fontsize=12)
axes[1, 0].set_ylabel('Mean Absolute Error', fontsize=12)
axes[1, 0].tick_params(axis='x', rotation=0)

# Plot 4: C6H6 Errors by Hour
error_by_hour['Abs_Diff_C6H6'].plot(kind='bar', ax=axes[1, 1])
axes[1, 1].set_title('Mean Absolute Error (C6H6) by Hour', fontsize=14)
axes[1, 1].set_xlabel('Hour of Day', fontsize=12)
axes[1, 1].set_ylabel('Mean Absolute Error', fontsize=12)
axes[1, 1].tick_params(axis='x', rotation=0)

# Plot 5: CO Errors by Weekday
error_by_weekday['Abs_Diff_CO'].plot(kind='bar', ax=axes[2, 0])
axes[2, 0].set_title('Mean Absolute Error (CO) by Weekday', fontsize=14)
axes[2, 0].set_xlabel('Day of the Week', fontsize=12)
axes[2, 0].set_ylabel('Mean Absolute Error', fontsize=12)
axes[2, 0].tick_params(axis='x', rotation=45)

# Plot 6: C6H6 Errors by Weekday
error_by_weekday['Abs_Diff_C6H6'].plot(kind='bar', ax=axes[2, 1])
axes[2, 1].set_title('Mean Absolute Error (C6H6) by Weekday', fontsize=14)
axes[2, 1].set_xlabel('Day of the Week', fontsize=12)
axes[2, 1].set_ylabel('Mean Absolute Error', fontsize=12)
axes[2, 1].tick_params(axis='x', rotation=45)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig("residual_analysis_v3.png", dpi=100) # Save to new file
print("\nResidual plots saved to 'residual_analysis_v3.png'")

print("\n--- Analysis Complete ---")