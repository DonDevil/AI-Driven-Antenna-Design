import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import MeanSquaredError
import joblib

def prepare_training_data(df):
    numeric_features = df[['patch_W', 'patch_L', 'eps_eff', 'substrate_h', 'eps_r', 'feed_width_m']].values
    feed_type = df['feed_type'].values.reshape(-1, 1)
    encoder = OneHotEncoder(sparse_output=False)
    feed_type_onehot = encoder.fit_transform(feed_type)
    X = np.hstack([numeric_features, feed_type_onehot])
    y = df[['freq_Hz', 'bandwidth_Hz']].values
    y[:, 0] = y[:, 0] / 1e9  # Convert Hz to GHz
    y[:, 1] = y[:, 1] / 1e6  # Convert Hz to MHz
    return X, y, encoder

def build_model(input_dim):
    model = Sequential([
        Dense(64, activation='relu', input_shape=(input_dim,)),
        Dense(32, activation='relu'),
        Dense(2)  # Predict frequency and bandwidth
    ])
    model.compile(optimizer='adam', loss=MeanSquaredError())
    return model

if __name__ == "__main__":
    print("Loading dataset.csv...")
    df = pd.read_csv(r"dataset\dataset.csv")
    X, y, encoder = prepare_training_data(df)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    print("Training forward model...")
    model = build_model(X_train.shape[1])
    model.fit(X_train, y_train, epochs=50, batch_size=64, validation_split=0.1)

    test_loss = model.evaluate(X_test, y_test)
    print(f"Forward model test loss: {test_loss}")

    # Save artifacts
    model.save(r"models\forward-predict\forward_model.h5")
    joblib.dump(scaler, r"models\forward-predict\forward_scaler.save")
    joblib.dump(encoder, r"models\forward-predict\forward_encoder.save")
    print("Forward model and preprocessors saved.")
