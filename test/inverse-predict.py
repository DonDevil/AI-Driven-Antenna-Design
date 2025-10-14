import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import MeanSquaredError
import joblib

def prepare_inverse_training_data(df):
    freq_bw = df[['freq_Hz', 'bandwidth_Hz']].values
    freq_bw[:, 0] = freq_bw[:, 0] / 1e9  # Hz → GHz
    freq_bw[:, 1] = freq_bw[:, 1] / 1e6  # Hz → MHz

    antenna_params = df[['patch_W', 'patch_L', 'eps_eff', 'substrate_h', 'eps_r', 'feed_width_m']].values
    feed_type = df['feed_type'].values.reshape(-1, 1)
    encoder = OneHotEncoder(sparse_output=False)
    feed_type_onehot = encoder.fit_transform(feed_type)

    y = np.hstack([antenna_params, feed_type_onehot])
    return freq_bw, y, encoder

def build_inverse_model(input_dim, output_dim):
    model = Sequential([
        Dense(64, activation='relu', input_shape=(input_dim,)),
        Dense(64, activation='relu'),
        Dense(output_dim)
    ])
    model.compile(optimizer='adam', loss=MeanSquaredError())
    return model

if __name__ == "__main__":
    print("Loading dataset.csv...")
    df = pd.read_csv(r"dataset\dataset.csv")

    X_inv, y_inv, encoder = prepare_inverse_training_data(df)

    scaler_inv = StandardScaler()
    X_inv_scaled = scaler_inv.fit_transform(X_inv)

    X_train_inv, X_test_inv, y_train_inv, y_test_inv = train_test_split(X_inv_scaled, y_inv, test_size=0.2, random_state=42)

    print("Training inverse model...")
    inv_model = build_inverse_model(input_dim=2, output_dim=y_inv.shape[1])
    inv_model.fit(X_train_inv, y_train_inv, epochs=100, batch_size=64, validation_split=0.1)

    test_loss = inv_model.evaluate(X_test_inv, y_test_inv)
    print(f"Inverse model test loss: {test_loss}")

    # Save artifacts
    inv_model.save(r"models\inverse-predict\inverse_model.h5")
    joblib.dump(scaler_inv, r"models\inverse-predict\inverse_scaler.save")
    joblib.dump(encoder, r"models\inverse-predict\inverse_encoder.save")
    print("Inverse model and preprocessors saved.")
