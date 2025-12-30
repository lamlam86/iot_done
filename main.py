import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import time
import optuna
import matplotlib.pyplot as plt  # <-- Added for analysis
import seaborn as sns
import joblib          # <-- Added for analysis

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
df['C6H6_roll_mean_3hr'] = df['C6H6(GT)'].shift(1).rolling(window=3).mean()

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


print("Creating 'state' features (daytime, rush hour)...")
# Feature 1: Is it daytime?
# Let's define daytime as 7:00 (7am) to 20:00 (8pm)
df['is_daytime'] = ((df['Hour'] >= 7) & (df['Hour'] <= 20)).astype(int)
# Feature 2: Is it morning rush hour?
df['is_morning_rush'] = ((df['Hour'] >= 7) & (df['Hour'] <= 9)).astype(int)
# Feature 3: Is it evening rush hour?
df['is_evening_rush'] = ((df['Hour'] >= 17) & (df['Hour'] <= 19)).astype(int)

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
    'C6H6_diff_x_hour_sin', 'C6H6_diff_x_hour_cos', # Added all interactions
    'CO_diff_x_hour_sin', 'CO_diff_x_hour_cos',
    'is_daytime',
    'is_morning_rush',
    'is_evening_rush'
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
# NOTE: This section is defined but not run,
# as we are using the pre-found parameters.
# This is correct.
print("\n--- Step 5: Skipping Optuna Tuning (Using Pre-Found Params) ---")

# We normalize the MAE score so both models are weighted fairly
# Use your last script's MAE values as a baseline
BASELINE_MAE_CO = 0.37 
BASELINE_MAE_C6H6 = 1.63

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

# --- Step 6: Train FINAL Models with Best Params ---
print("\n--- Step 6: Training Final Models with Best Parameters ---")

# The best parameters you found:
best_params = {
    'learning_rate': 0.03065092459457942, 
    'depth': 5, 
    'l2_leaf_reg': 1.869560153272358, 
    'subsample': 0.7367462866287637
}
best_params['iterations'] = 3000          
best_params['early_stopping_rounds'] = 200 
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

from sklearn.metrics import mean_squared_error

print("\n--- Step 9: Visualization of Metrics ---")

# 1. Calculate missing metrics (Individual R2 and RMSE)
# Your script already calculated MAE, but we need RMSE and individual R2s for the plots
r2_co = r2_score(y_test['CO(GT)'], y_pred_actual[:, 0])
r2_c6h6 = r2_score(y_test['C6H6(GT)'], y_pred_actual[:, 1])

rmse_co = np.sqrt(mean_squared_error(y_test['CO(GT)'], y_pred_actual[:, 0]))
rmse_c6h6 = np.sqrt(mean_squared_error(y_test['C6H6(GT)'], y_pred_actual[:, 1]))

# 2. Organize data for plotting into a DataFrame
metrics_df = pd.DataFrame({
    'Target': ['CO(GT)', 'CO(GT)', 'CO(GT)', 'C6H6(GT)', 'C6H6(GT)', 'C6H6(GT)'],
    'Metric': ['R2', 'MAE', 'RMSE', 'R2', 'MAE', 'RMSE'],
    'Value': [r2_co, mae_co, rmse_co, r2_c6h6, mae_c6h6, rmse_c6h6]
})

print("Metrics Summary:")
print(metrics_df)

# 3. Plot R-Squared Scores
# We plot R2 separately because its scale (0-1) is different from the error metrics
plt.figure(figsize=(8, 5))
ax1 = sns.barplot(data=metrics_df[metrics_df['Metric'] == 'R2'], x='Target', y='Value', palette='viridis')
plt.title('R-Squared (R2) Score by Target')
plt.ylim(0, 1.1)  # Set limit slightly above 1 for annotations
plt.ylabel('R2 Score')
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Add value labels on top of bars
for p in ax1.patches:
    ax1.annotate(f'{p.get_height():.3f}', 
                 (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha='center', va='center', fontsize=12, color='black', xytext=(0, 5),
                 textcoords='offset points')

plt.tight_layout()
plt.savefig('metric_R2.png')
plt.show()

# 4. Plot MAE and RMSE together
plt.figure(figsize=(10, 6))
error_df = metrics_df[metrics_df['Metric'].isin(['MAE', 'RMSE'])]
ax2 = sns.barplot(data=error_df, x='Target', y='Value', hue='Metric', palette='rocket')

plt.title('Error Metrics (MAE & RMSE)')
plt.ylabel('Error Value (Lower is Better)')
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Add value labels
for p in ax2.patches:
    ax2.annotate(f'{p.get_height():.3f}', 
                 (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha='center', va='center', fontsize=10, color='black', xytext=(0, 5),
                 textcoords='offset points')

plt.tight_layout()
plt.savefig('metric_MAE_RMSE.png')
plt.show()

print("Plots saved as 'metric_R2.png' and 'metric_MAE_RMSE.png'")

print("\n--- Step 10: Visualizing Train vs. Validation Loss ---")

# 1. Extract training history
# CatBoost defaults to RMSE if no other metric is specified
results_co = model_co.get_evals_result()
results_c6h6 = model_c6h6.get_evals_result()

# 2. Setup the plot (2 subplots side-by-side)
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# --- Plot for CO(GT) ---
# The keys are typically 'learn' and 'validation'
# The metric inside is 'RMSE' by default for Regressors
train_rmse_co = results_co['learn']['RMSE']
val_rmse_co = results_co['validation']['RMSE']
epochs_co = range(len(train_rmse_co))

axes[0].plot(epochs_co, train_rmse_co, label='Training Loss', color='blue')
axes[0].plot(epochs_co, val_rmse_co, label='Validation Loss', color='orange')
axes[0].set_title('CO(GT): Train vs Validation Loss')
axes[0].set_xlabel('Iterations')
axes[0].set_ylabel('RMSE')
axes[0].legend()
axes[0].grid(True, linestyle='--', alpha=0.5)

# --- Plot for C6H6(GT) ---
train_rmse_c6 = results_c6h6['learn']['RMSE']
val_rmse_c6 = results_c6h6['validation']['RMSE']
epochs_c6 = range(len(train_rmse_c6))

axes[1].plot(epochs_c6, train_rmse_c6, label='Training Loss', color='blue')
axes[1].plot(epochs_c6, val_rmse_c6, label='Validation Loss', color='orange')
axes[1].set_title('C6H6(GT): Train vs Validation Loss')
axes[1].set_xlabel('Iterations')
axes[1].set_ylabel('RMSE')
axes[1].legend()
axes[1].grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('train_val_loss.png')
plt.show()

print("Loss plot saved as 'train_val_loss.png'")