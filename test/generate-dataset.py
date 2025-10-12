import numpy as np
import pandas as pd

c = 3e8  # Speed of light in m/s

def calculate_patch_params(f_r, eps_r, h):
    W = (c / (2 * f_r)) * np.sqrt(2 / (eps_r + 1))
    eps_eff = (eps_r + 1)/2 + (eps_r - 1)/2 * (1 + 12*h/W)**-0.5
    delta_L = 0.412 * h * ((eps_eff + 0.3)*(W/h + 0.264))/((eps_eff - 0.258)*(W/h + 0.8))
    L = (c / (2 * f_r * np.sqrt(eps_eff))) - 2*delta_L
    BW_frac = (1.5 * h / W) * np.sqrt(eps_r)
    BW = BW_frac * f_r
    return W, L, eps_eff, BW

def generate_dataset(samples=10000, random_state=42):
    np.random.seed(random_state)
    freqs = np.random.uniform(1e9, 5e9, samples)
    eps_r_vals = np.random.uniform(2.0, 10.0, samples)
    h_vals = np.random.uniform(0.0005, 0.003, samples)
    fw_vals = np.random.uniform(0.001, 0.006, samples)
    feed_types = np.random.choice([0,1,2,3], samples)
    feed_bw_factors = {0: 1.0, 1: 0.9, 2: 1.1, 3: 1.05}

    data = []
    for f_r, eps_r, h, fw, ft in zip(freqs, eps_r_vals, h_vals, fw_vals, feed_types):
        W, L, eps_eff, BW = calculate_patch_params(f_r, eps_r, h)
        BW_adj = BW * feed_bw_factors[ft]
        data.append([f_r, eps_r, h, fw, ft, W, L, eps_eff, BW_adj])

    df = pd.DataFrame(data, columns=[
        'freq_Hz', 'eps_r', 'substrate_h', 'feed_width_m',
        'feed_type', 'patch_W', 'patch_L', 'eps_eff', 'bandwidth_Hz'])
    return df

if __name__ == "__main__":
    print("Generating synthetic dataset...")
    df = generate_dataset()
    df.to_csv(r"dataset\dataset.csv", index=False)
    print("Dataset saved to dataset.csv")
