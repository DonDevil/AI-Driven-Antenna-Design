from models.trainer import ModelTrainer
from models.predictor import Predictor
from models.optimizer import Optimizer
from cst_interface.sweep import SweepManager
from cst_interface.builders.patch import PatchBuilder


def main():
    while True:
        print("\n=== AI Antenna Design Assistant ===")
        print("1. Design new antenna")
        print("2. Optimize existing antenna")
        print("3. Train ANN model from CST sweeps")
        print("4. Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            family = input("Enter antenna family (patch/slot/dipole): ").strip().lower()
            material = input("Enter substrate material: ").strip()
            target_freq = float(input("Enter target resonant frequency (GHz): "))

            predictor = Predictor(family)
            if not predictor.model_exists():
                print(f"No ANN model for {family}, running CST sweep + training...")
                sweep = SweepManager(family)
                sweep.run_sweep()
                trainer = ModelTrainer(family)
                trainer.train()

            params = predictor.inverse_design(target_freq)
            print(f"Predicted parameters: {params}")

            if family == "patch":
                PatchBuilder(params, material).build()
                print("Patch antenna created in CST.")

        elif choice == "2":
            family = input("Enter antenna family (patch/slot/dipole): ").strip().lower()
            goal = input("Optimization goal (freq/bandwidth/dip): ").strip().lower()
            target = float(input("Target value (GHz or bandwidth): "))

            predictor = Predictor(family)
            params = {}  # TODO: load actual parameters from CST project or file
            optimizer = Optimizer(family, goal)
            new_params = optimizer.optimize(params, target)
            print("Optimized parameters:", new_params)

        elif choice == "3":
            family = input("Enter antenna family to train (patch/slot/dipole): ").strip().lower()
            trainer = ModelTrainer(family)
            trainer.train()
            print(f"Training completed for {family} antenna model.")

        elif choice == "4":
            print("Exiting AI Antenna Design Assistant. Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
