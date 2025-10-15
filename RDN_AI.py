import numpy as np
import joblib
from tensorflow.keras.models import load_model
import scipy.optimize

class TrainedAI:
    def __init__(self, model_path="models"):
        print("AI Initialized")
    
    def optimize_parameters(self, desired_freq_ghz, desired_bw_mhz, **fixed_params):
        """
        General optimization: keeps any provided parameter(s) constant, optimizes others to match freq/bandwidth.
        Usage: optimize_parameters(2.4, 100, eps_r=4.4, substrate_h=0.0016)
        """
        # All possible parameter names (order must match model input)
        param_names = ['patch_W', 'patch_L', 'eps_eff', 'substrate_h', 'eps_r', 'feed_width_m', 'feed_type']
        # Initial guess for all params (can be improved)
        x0 = [0.03, 0.03, 3.0, 0.001, 4.0, 0.002, 0]  # reasonable defaults
        bounds = [(0.001, 0.1), (0.001, 0.1), (1.0, 10.0), (0.0005, 0.003), (2.0, 10.0), (0.001, 0.006), (0, 3)]
        # Identify fixed and variable indices
        fixed_indices = {i: fixed_params[n] for i, n in enumerate(param_names) if n in fixed_params}
        variable_indices = [i for i in range(len(param_names)) if i not in fixed_indices]
        # Prepare initial guess and bounds for variables only
        x0_var = [x0[i] for i in variable_indices]
        bounds_var = [bounds[i] for i in variable_indices]
        # Load model/scaler/encoder
        self.model = load_model(r"models\forward-predict\forward_model.h5")
        self.scaler = joblib.load(r"models\forward-predict\forward_scaler.save")
        self.encoder = joblib.load(r"models\forward-predict\forward_encoder.save")
        freq_norm = 10.0  # GHz
        bw_norm = 100.0   # MHz
        def objective(x_var):
            # Build full param vector
            params = x0[:]
            for idx, val in zip(variable_indices, x_var):
                params[idx] = val
            for idx, val in fixed_indices.items():
                params[idx] = val
            # One-hot encode feed_type
            feed_type_onehot = self.encoder.transform([[int(params[6])]])
            input_vector = np.hstack([params[:6], feed_type_onehot.flatten()]).reshape(1, -1)
            input_scaled = self.scaler.transform(input_vector)
            pred = self.model.predict(input_scaled)
            freq_pred_ghz = pred[0][0]
            bw_pred_mhz = pred[0][1]
            # Prioritize frequency error (weight = 10), bandwidth error (weight = 1)
            freq_error = (freq_pred_ghz - desired_freq_ghz) / freq_norm
            bw_error = (bw_pred_mhz - desired_bw_mhz) / bw_norm
            return 10 * freq_error**2 + 1 * bw_error**2

        # Run optimization
        result = scipy.optimize.minimize(
            objective, x0_var, bounds=bounds_var, method='Powell',
            options={'maxiter': 1000, 'disp': True}
        )
        # Build final param dict
        final_params = x0[:]
        for idx, val in zip(variable_indices, result.x):
            final_params[idx] = val
        for idx, val in fixed_indices.items():
            final_params[idx] = val
        # Decode feed_type label
        feed_type_index = int(final_params[6])
        feed_type_label = self.encoder.categories_[0][feed_type_index]
        L_s = final_params[1] + 6*final_params[3]
        W_s = final_params[0] + 6*final_params[3]
        return {
            "patch_W": final_params[0],
            "patch_L": final_params[1],
            "eps_eff": final_params[2],
            "substrate_h": final_params[3],
            "substrate_W": W_s,
            "substrate_L": L_s,
            "eps_r": final_params[4],
            "feed_width": final_params[5],
            "feed_type": feed_type_label,
            "success": result.success,
            "fun": result.fun
        }

    def predict_input(self, desired_freq_ghz, desired_bw_mhz):
        self.inv_model = load_model(r"models\inverse-predict\inverse_model.h5")
        self.inv_scaler = joblib.load(r"models\inverse-predict\inverse_scaler.save")
        self.inv_encoder = joblib.load(r"models\inverse-predict\inverse_encoder.save")
        input_vec = np.array([[desired_freq_ghz, desired_bw_mhz]])
        input_scaled = self.inv_scaler.transform(input_vec)
        pred = self.inv_model.predict(input_scaled)[0]
        
        # Split outputs
        params = pred[:6]
        feed_type_encoded = pred[6:]
        
        feed_type_index = np.argmax(feed_type_encoded)
        feed_type_label = self.inv_encoder.categories_[0][feed_type_index]
        
        L_s = params[1] + 6*params[3]
        W_s = params[0] + 6*params[3]
        return {
            "patch_W": params[0],
            "patch_L": params[1],
            "eps_eff": params[2],
            "substrate_h": params[3],
            "substrate_W": W_s,
            "substrate_L": L_s,
            "eps_r": params[4],
            "feed_width": params[5],
            "feed_type": feed_type_label,
        }


    def predict_output(self, patch_W, patch_L, eps_eff, substrate_h, eps_r, feed_width_m, feed_type_int):
        self.model = load_model(r"models\forward-predict\forward_model.h5")
        self.scaler = joblib.load(r"models\forward-predict\forward_scaler.save")
        self.encoder = joblib.load(r"models\forward-predict\forward_encoder.save")
        feed_type_onehot = self.encoder.transform([[feed_type_int]])
        input_vector = np.hstack([[patch_W, patch_L, eps_eff, substrate_h, eps_r, feed_width_m], feed_type_onehot.flatten()]).reshape(1, -1)
        input_scaled = self.scaler.transform(input_vector)
        pred = self.model.predict(input_scaled)
        freq_pred_ghz = pred[0][0]
        bw_pred_mhz = pred[0][1]
        return freq_pred_ghz, bw_pred_mhz
'''
ai = TrainedAI()
r1 = ai.predict_input(2.4, 100)
r2 = ai.optimize_parameters(2.4, 100, eps_r=4.4, substrate_h=0.0016)
pw = r1['patch_W']
pl = r1['patch_L']
ee = r1['eps_eff']
sh = r1['substrate_h']
er = r1['eps_r']
fw = r1['feed_width_m']
ft = r1['feed_type']
r3 = ai.predict_output(pw, pl, ee, sh, er, fw, ft)
pw = r2['patch_W']
pl = r2['patch_L']
ee = r2['eps_eff']
sh = r2['substrate_h']
er = r2['eps_r']
fw = r2['feed_width_m']
ft = r2['feed_type']
r4 = ai.predict_output(pw, pl, ee, sh, er, fw, ft)
print(r1)
print("--------------------------")
print(r2)
print("--------------------------")
print(r3)
print("--------------------------")
print(r4)
'''