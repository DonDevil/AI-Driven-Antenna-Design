import numpy as np

# Substrate database: (eps_r, thickness in meters)
substrates = {
    'FR4': (4.4, 0.0016),
    'Rogers4350': (3.66, 0.001524),
    'Rogers5880': (2.2, 0.00157),
    'TaconicTLY': (2.2, 0.0015)
}

def patch_antenna_params(f_r, eps_r, h, R0=50):
    """Calculate patch antenna parameters with 50Ω inset feed."""
    c = 3e8  # speed of light

    # Patch width
    W = (c / (2 * f_r)) * np.sqrt(2 / (eps_r + 1))

    # Effective dielectric constant
    eps_eff = (eps_r + 1)/2 + (eps_r - 1)/2 * (1 + 12*h/W)**(-0.5)

    # Length extension
    delta_L = 0.412 * h * ((eps_eff + 0.3)*(W/h + 0.264))/((eps_eff - 0.258)*(W/h + 0.8))

    # Patch length
    L = (c / (2 * f_r * np.sqrt(eps_eff))) - 2*delta_L

    # Substrate (ground) dimensions
    L_s = L + 6*h
    W_s = W + 6*h

    # Approximate input resistance at patch edge
    Rin_edge = 90 * (W/L)**2
    if Rin_edge < R0:
        y0 = 0  # cannot match, use edge feed
    else:
        y0 = (L/np.pi) * np.arccos(np.sqrt(R0/Rin_edge))

    return W, L, W_s, L_s, y0

def design_patch(frequency_ghz, substrate_name, R0=50):
    """Design a patch antenna for a given frequency and user-selected substrate."""
    if substrate_name not in substrates:
        raise ValueError(f"Unknown substrate: {substrate_name}")

    eps_r, h = substrates[substrate_name]
    f_r = frequency_ghz * 1e9  # Convert GHz to Hz

    W, L, W_s, L_s, y0 = patch_antenna_params(f_r, eps_r, h, R0)

    return {
        'frequency_GHz': frequency_ghz,
        'substrate': substrate_name,
        'eps_r': eps_r,
        'substrate_thickness_m': h,
        'patch_width_m': W,
        'patch_length_m': L,
        'substrate_width_m': W_s,
        'substrate_length_m': L_s,
        'inset_feed_m': y0
    }

# Example usage
def calculate_rect(desired_freq, selected_substrate):
    desired_freq = float(desired_freq)  # Convert to float, GHz
    selected_substrate = selected_substrate  # from user selection
    antenna = design_patch(desired_freq, selected_substrate)

    return antenna