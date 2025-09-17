class Optimizer:
    def __init__(self, family: str, goal: str):
        self.family = family
        self.goal = goal

    def optimize(self, params: dict, target: float):
        # run optimization loop
        print("Optimizing the Design")
