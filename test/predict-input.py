import numpy as np
import joblib
from tensorflow.keras.models import load_model

# Load saved inverse model and preprocessors
inv_model = load_model(r"models\inverse-predict\inverse_model.h5")
inv_scaler = joblib.load(r"models\inverse-predict\inverse_scaler.save")
inv_encoder = joblib.load(r"models\inverse-predict\inverse_encoder.save")

def inverse_predict(desired_freq_ghz, desired_bw_mhz):
    input_vec = np.array([[desired_freq_ghz, desired_bw_mhz]])
    input_scaled = inv_scaler.transform(input_vec)
    pred = inv_model.predict(input_scaled)[0]
    
    # Split outputs
    params = pred[:6]
    feed_type_encoded = pred[6:]
    
    feed_type_index = np.argmax(feed_type_encoded)
    feed_type_label = inv_encoder.categories_[0][feed_type_index]
    
    return {
        'patch_W': params[0],
        'patch_L': params[1],
        'eps_eff': params[2],
        'substrate_h': params[3],
        'eps_r': params[4],
        'feed_width_m': params[5],
        'feed_type': feed_type_label
    }

# Example usage:
design_params = inverse_predict(2.4, 100)
print("Predicted antenna parameters:", design_params)
