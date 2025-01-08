class PIDController:
    def __init__(self, kp=1.0, tau=1.0, theta=0.0):
        """Initialize the PID controller with default or specified parameters."""
        self.kp = kp
        self.tau = tau
        self.theta = theta
        self.kc = None
        self.ki = None
        self.kd = None
        self.fine_tune = True

    def set_parameters(self, kp, tau, theta):
        """Set the model parameters."""
        self.kp = kp
        self.tau = tau
        self.theta = theta

    def calculate(self, method="Fine Tune", val=1):
        """Calculate PID parameters based on the selected method."""
        if method == "Fine Tune":
            # Placeholder equations for fine-tuning
            self.kc = 1.0  # Replace with actual logic
            self.ki = 1.0  # Replace with actual logic
            self.kd = val  # Replace with actual logic
        elif method == "Detune":
            # Placeholder equations for detuning
            self.kc = 0.5  # Replace with actual logic
            self.ki = 0.5  # Replace with actual logic
            self.kd = val  # Replace with actual logic
        else:
            print("Invalid method selected. Use 'fine_tune' or 'detune'.")

        print(f"Method: {method}")
        print(f"Kc: {self.kc}, Ki: {self.ki}, Kd: {self.kd}")

    def reset(self):
        """Reset the internal state of the controller."""
        self.kc = None
        self.ki = None
        self.kd = None

# Example usage:
# pid = PIDController()
# pid.set_parameters(2.0, 0.5, 1.0)

# Fine-tune method
# pid.calculate(method="fine_tune")

# Detune method
# pid.calculate(method="detune")
