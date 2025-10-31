import os
import csv
import time
import joblib
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split

# adjust paths to your models directory if needed
FORWARD_MODEL_PATH = r"models\forward-predict\forward_model.h5"
FORWARD_SCALER_PATH = r"models\forward-predict\forward_scaler.save"
FORWARD_ENCODER_PATH = r"models\forward-predict\forward_encoder.save"

INVERSE_MODEL_PATH = r"models\inverse-predict\inverse_model.h5"
INVERSE_SCALER_PATH = r"models\inverse-predict\inverse_scaler.save"
INVERSE_ENCODER_PATH = r"models\inverse-predict\inverse_encoder.save"

FEEDBACK_FILE = "ai_feedback_log.csv"
RETRAIN_MIN_SAMPLES = 12        # retrain when we have at least this many feedback rows
RETRAIN_ON_EVERY = 8           # retrain every N new entries after min reached
AUTOCORRECT_DAMPING = 0.6      # damping for auto-correction (0..1). 1=full correction, 0=none

class TrainedAI:
    def __init__(self, models_dir="models"):
        print("AI Initialized")
        # lazy-load models when needed
        self._forward_loaded = False
        self._inverse_loaded = False
        self._load_forward()
        self._load_inverse()
        # count new feedbacks since last retrain (persistent across runs if file exists)
        self._feedback_count = 0
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, newline="") as f:
                    self._feedback_count = sum(1 for _ in f) - 1  # minus header
            except Exception:
                self._feedback_count = 0

    # ---------- model load helpers ----------
    def _load_forward(self):
        if self._forward_loaded:
            return
        if os.path.exists(FORWARD_MODEL_PATH):
            self.model = load_model(FORWARD_MODEL_PATH)
            self.scaler = joblib.load(FORWARD_SCALER_PATH)
            self.encoder = joblib.load(FORWARD_ENCODER_PATH)
            self._forward_loaded = True
        else:
            self.model = None
            self.scaler = None
            self.encoder = None
            self._forward_loaded = False

    def _load_inverse(self):
        if self._inverse_loaded:
            return
        if os.path.exists(INVERSE_MODEL_PATH):
            self.inv_model = load_model(INVERSE_MODEL_PATH)
            self.inv_scaler = joblib.load(INVERSE_SCALER_PATH)
            self.inv_encoder = joblib.load(INVERSE_ENCODER_PATH)
            self._inverse_loaded = True
        else:
            self.inv_model = None
            self.inv_scaler = None
            self.inv_encoder = None
            self._inverse_loaded = False

    # ---------- logging ----------
    def _ensure_feedback_header(self, num_params=6):
        if not os.path.exists(FEEDBACK_FILE):
            header = ["timestamp", "target_Fr_GHz", "target_BW_MHz"]
            header += [f"param_{i}" for i in range(num_params)]
            header += ["feed_type_label", "actual_Fr_GHz", "actual_BW_MHz", "S11_dB"]
            with open(FEEDBACK_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)

    def log_feedback(self, target_Fr, target_BW, predicted_params, feed_type_label, actual_Fr, actual_BW, S11):
        """
        Append one feedback row to CSV.
        predicted_params: list/array of first 6 numeric parameters [W,L,eps_eff,substrate_h,eps_r,feed_width]
        feed_type_label: string label from encoder/categories_
        """
        try:
            self._ensure_feedback_header(num_params=len(predicted_params))
            row = [time.time(), float(target_Fr), float(target_BW)]
            row += [float(x) for x in predicted_params[:6]]
            row += [str(feed_type_label), float(actual_Fr), float(actual_BW), float(S11)]
            with open(FEEDBACK_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)
            self._feedback_count += 1
        except Exception as e:
            print("[AI][log_feedback] failed:", e)

    # ---------- auto-correction ----------
    def autocorrect_params(self, predicted_params, desired_Fr, actual_Fr, desired_BW=None, actual_BW=None):
        """
        Simple physics-guided correction:
        - Resonant frequency f ~ 1/(2*L*sqrt(eps_eff)), so L ∝ 1/f.
          We'll scale patch_L and patch_W by ratio r = actual/desired (damped).
        - Bandwidth correction: weak heuristic scaling of feed_width depending on BW ratio.
        Returns corrected_params list (same length as predicted_params).
        """
        params = predicted_params[:]  # copy
        try:
            # frequency ratio: if actual < desired => ratio < 1 => reduce length to raise freq
            r = float(actual_Fr) / float(desired_Fr) if desired_Fr != 0 else 1.0
            # desired correction multiplier to apply to linear dimensions:
            # new = old * (actual/desired) -> then damp toward new by AUTOCORRECT_DAMPING
            # compute correction multiplier
            corr_mult = r
            damp = AUTOCORRECT_DAMPING
            # apply to patch_L (index 1) and patch_W (index 0)
            params[1] = params[1] * ( (1-damp) + damp * corr_mult )
            params[0] = params[0] * ( (1-damp) + damp * corr_mult )

            # Bandwidth correction (if data present) -> adjust feed width slightly
            if desired_BW is not None and actual_BW is not None and actual_BW > 0:
                bw_ratio = float(desired_BW) / float(actual_BW)
                # modest scaling on feed width; sqrt to avoid large jumps
                feed_corr = (bw_ratio**0.5)
                params[5] = params[5] * ( (1-damp) + damp * feed_corr )

            # keep values in sane bounds (you can tune these)
            params[0] = float(np.clip(params[0], 0.001, 0.12))  # patch_W
            params[1] = float(np.clip(params[1], 0.001, 0.12))  # patch_L
            params[5] = float(np.clip(params[5], 0.0005, 0.01)) # feed_width
        except Exception as e:
            print("[AI][autocorrect] failed:", e)
        return params

    # ---------- retraining ----------
    def retrain_if_needed(self, min_samples=RETRAIN_MIN_SAMPLES, retrain_every=RETRAIN_ON_EVERY):
        """
        Retrain forward model on feedback CSV (predictors: target + params -> actual outputs)
        We'll train a small MLPRegressor from scikit-learn for robustness if keras unavailable for quick retrain.
        This function is synchronous and may take time depending on sample count.
        """
        try:
            if not os.path.exists(FEEDBACK_FILE):
                return False
            import pandas as pd
            df = pd.read_csv(FEEDBACK_FILE)
            # drop rows with NaN
            df = df.dropna()
            n = len(df)
            if n < min_samples:
                return False
            # Only retrain every `retrain_every` new samples to avoid retraining too frequently
            if n < self._feedback_count:  # shouldn't happen
                pass
            # if we retrained recently (self._last_retrain_count variable), skip unless enough new rows
            # store last retrain count in file .ai_retrain_meta
            meta_path = ".ai_retrain_meta"
            last = 0
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        last = int(f.read().strip() or "0")
                except Exception:
                    last = 0
            if (n - last) < retrain_every:
                return False

            # Prepare X and y:
            # X: [target_Fr, target_BW, param_0..param_5] -> these are inputs we used originally
            # y: [actual_Fr, actual_BW]
            cols = list(df.columns)
            # expected columns present by logger: timestamp, target_Fr_GHz, target_BW_MHz, param_0..param_5, feed_type_label, actual_Fr_GHz, actual_BW_MHz, S11_dB
            if "actual_Fr_GHz" not in df.columns:
                # try to be flexible with names
                if "actual_Fr" in df.columns:
                    df.rename(columns={"actual_Fr":"actual_Fr_GHz"}, inplace=True)
            X_cols = ["target_Fr_GHz", "target_BW_MHz"] + [c for c in df.columns if c.startswith("param_")]
            y_cols = ["actual_Fr_GHz", "actual_BW_MHz"]
            X = df[X_cols].values
            y = df[y_cols].values

            # simple normalization
            X_mean = X.mean(axis=0)
            X_std = X.std(axis=0) + 1e-9
            Xn = (X - X_mean) / X_std
            y_mean = y.mean(axis=0)
            y_std = y.std(axis=0) + 1e-9
            yn = (y - y_mean) / y_std

            # small MLP with scikit-learn for quick retrain
            from sklearn.neural_network import MLPRegressor
            mdl = MLPRegressor(hidden_layer_sizes=(256,128), max_iter=600, random_state=42)
            mdl.fit(Xn, yn)

            # save retrained model and scalers for usage in quick-correct step
            joblib.dump({
                "sk_model": mdl,
                "X_mean": X_mean,
                "X_std": X_std,
                "y_mean": y_mean,
                "y_std": y_std
            }, "ai_quick_retrain.save")
            # update retrain meta
            with open(meta_path, "w") as f:
                f.write(str(n))
            print(f"[AI][retrain] retrained on {n} feedback samples and saved ai_quick_retrain.save")
            return True
        except Exception as e:
            print("[AI][retrain_if_needed] failed:", e)
            return False

    # ---------- your existing methods updated ----------
    def predict_input(self, desired_freq_ghz, desired_bw_mhz):
        self._load_inverse()
        if not self._inverse_loaded:
            raise RuntimeError("Inverse model not found.")
        input_vec = np.array([[desired_freq_ghz, desired_bw_mhz]])
        input_scaled = self.inv_scaler.transform(input_vec)
        pred = self.inv_model.predict(input_scaled)[0]

        params = pred[:6].tolist()
        feed_type_encoded = pred[6:]
        feed_type_index = int(np.argmax(feed_type_encoded))
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
        self._load_forward()
        if not self._forward_loaded:
            raise RuntimeError("Forward model not found.")
        feed_type_onehot = self.encoder.transform([[feed_type_int]])
        input_vector = np.hstack([[patch_W, patch_L, eps_eff, substrate_h, eps_r, feed_width_m], feed_type_onehot.flatten()]).reshape(1, -1)
        input_scaled = self.scaler.transform(input_vector)
        pred = self.model.predict(input_scaled)
        freq_pred_ghz = float(pred[0][0])
        bw_pred_mhz = float(pred[0][1])
        return freq_pred_ghz, bw_pred_mhz

    def optimize_parameters(self, desired_freq_ghz, desired_bw_mhz, **fixed_params):
        """
        Keep compatibility with your previous optimize_parameters but make it return
        the numeric parameter vector (not the label) so we can log + autocorrect easily.
        """
        # same param order as your original code
        param_names = ['patch_W', 'patch_L', 'eps_eff', 'substrate_h', 'eps_r', 'feed_width_m', 'feed_type']
        # defaults similar to yours
        x0 = [0.03, 0.03, 3.0, 0.001, 4.0, 0.002, 0]  # reasonable defaults
        bounds = [(0.001, 0.1), (0.001, 0.1), (1.0, 10.0), (0.0005, 0.003), (2.0, 10.0), (0.001, 0.006), (0, 3)]
        fixed_indices = {i: fixed_params[n] for i, n in enumerate(param_names) if n in fixed_params}
        variable_indices = [i for i in range(len(param_names)) if i not in fixed_indices]
        x0_var = [x0[i] for i in variable_indices]
        bounds_var = [bounds[i] for i in variable_indices]

        # lazy load forward model
        self._load_forward()
        if not self._forward_loaded:
            raise RuntimeError("Forward model missing.")

        import scipy.optimize

        freq_norm = 10.0  # GHz
        bw_norm = 100.0   # MHz

        def objective(x_var):
            params = x0[:]
            for idx, val in zip(variable_indices, x_var):
                params[idx] = val
            for idx, val in fixed_indices.items():
                params[idx] = val
            # one-hot encode feed_type
            try:
                feed_type_onehot = self.encoder.transform([[int(params[6])]])
            except Exception:
                feed_type_onehot = self.encoder.transform([[0]])
            input_vector = np.hstack([params[:6], feed_type_onehot.flatten()]).reshape(1, -1)
            input_scaled = self.scaler.transform(input_vector)
            pred = self.model.predict(input_scaled)
            freq_pred_ghz = float(pred[0][0])
            bw_pred_mhz = float(pred[0][1])
            freq_error = (freq_pred_ghz - desired_freq_ghz) / freq_norm
            bw_error = (bw_pred_mhz - desired_bw_mhz) / bw_norm
            return 10 * freq_error**2 + 1 * bw_error**2

        result = scipy.optimize.minimize(
            objective, x0_var, bounds=bounds_var, method='Powell',
            options={'maxiter': 1000, 'disp': False}
        )

        final_params = x0[:]
        for idx, val in zip(variable_indices, result.x):
            final_params[idx] = float(val)
        for idx, val in fixed_indices.items():
            final_params[idx] = float(val)

        # decode feed_type label
        feed_type_index = int(round(final_params[6]))
        try:
            feed_type_label = self.encoder.categories_[0][feed_type_index]
        except Exception:
            feed_type_label = str(feed_type_index)

        L_s = final_params[1] + 6*final_params[3]
        W_s = final_params[0] + 6*final_params[3]

        # Return both numeric vector and a dict similar to old API
        return {
            "numeric": final_params[:6],    # first 6 numeric values (W,L,eps_eff,substrate_h,eps_r,feed_width)
            "feed_type_index": int(final_params[6]),
            "feed_type_label": feed_type_label,
            "dict": {
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
                "fun": float(result.fun)
            }
        }
'''
ai = TrainedAI()
#ai.predict_input(2.4, 100) 
r = ai.optimize_parameters(2.4, 100, patch_W=0.05)
print(r)
'''