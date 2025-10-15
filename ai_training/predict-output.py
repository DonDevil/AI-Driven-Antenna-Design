import numpy as np
import joblib
from tensorflow.keras.models import load_model

# Load saved model and preprocessors
model = load_model(r"models\forward-predict\forward_model.h5")
scaler = joblib.load(r"models\forward-predict\forward_scaler.save")
encoder = joblib.load(r"models\forward-predict\forward_encoder.save")

def forward_predict(patch_W, patch_L, eps_eff, substrate_h, eps_r, feed_width_m, feed_type_int):
    feed_type_onehot = encoder.transform([[feed_type_int]])
    input_vector = np.hstack([[patch_W, patch_L, eps_eff, substrate_h, eps_r, feed_width_m], feed_type_onehot.flatten()]).reshape(1, -1)
    input_scaled = scaler.transform(input_vector)
    pred = model.predict(input_scaled)
    freq_pred_ghz = pred[0][0]
    bw_pred_mhz = pred[0][1]
    return freq_pred_ghz, bw_pred_mhz

# Example usage:
freq, bw = forward_predict(0.04205455, 0.038612634, 3.214400, 0.0019071959, 3.21597, 0.006059286, 1)
print(f"Predicted Frequency: {freq} GHz, Bandwidth: {bw} MHz")
