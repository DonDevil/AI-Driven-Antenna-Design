class Predictor:
    def __init__(self, family: str):
        self.family = family

    def model_exists(self):
        # check if ANN exists for family
        print("Models Already Exists")

    def forward_predict(self, params: dict):
        # predict resonant freq from parameters
        print("Forward Predicitng for the Given Params")

    def inverse_design(self, target_freq: float):
        # predict parameters for given target freq
        print("Inverse Predicitng for the Given Freq")
