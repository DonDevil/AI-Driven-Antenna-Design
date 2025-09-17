class PatchBuilder:
    def __init__(self, params: dict, material: str):
        self.params = params
        self.material = material
    
    def build(self):
        print("Building Design in CST")