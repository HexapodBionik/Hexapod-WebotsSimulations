import numpy as np


class LegTrajectory:
    def __init__(self, leg_nb: int, step_length: float, step_height: float, movement_time: float, swing_percentage: float, input_position: np.ndarray):
        self._leg_nb = leg_nb
        self._step_length = step_length
        self._step_height = step_height
        self._input_position = input_position
        self._movement_time = movement_time
        self._swing_percentage = swing_percentage

        self._phase1_func = None
        self._phase2_func = None
        self._swing_y_func = None
        self._swing_z_func = None

    def generate_trajectory(self):
        swing_time = self._movement_time * self._swing_percentage
        stand_time = self._movement_time - swing_time

        phase_1_time = self._leg_nb * swing_time
        phase_2_time = self._movement_time - phase_1_time - swing_time

        if phase_1_time != stand_time:
            phase_1_length = (phase_1_time / self._movement_time) * self._step_length
        else:
            phase_1_length = self._step_length

        phase_2_length = (self._movement_time - phase_1_time) / self._movement_time * self._step_length

        # Solve for second part
        try:
            A2 = np.array([
                [phase_1_time + swing_time, 1],
                [self._movement_time, 1]
            ])

            b2 = np.array([phase_2_length, 0])
            x2 = np.linalg.solve(A2, b2)
            self._phase2_func = np.poly1d(x2)
        except Exception:
            pass


        if phase_1_time > 0:
            self._phase1_func = np.poly1d(np.array([-phase_1_length / phase_1_time, 0]))


        self._swing_y_func = lambda x: -(self._step_length / 2) + phase_1_length + (self._step_length / 2) * np.cos(x)


        self._swing_z_func = lambda x: self._step_height * np.sin(x)

    def generate_symmetrical_trajectory(self):
        swing_time = self._movement_time * self._swing_percentage
        phase_1_time = self._leg_nb * swing_time

        # Solve for second part
        try:
            A2 = np.array([
                [phase_1_time + swing_time, 1],
                [self._movement_time, 1]
            ])

            b2 = np.array([-self._step_length/2, self._input_position[1]])
            x2 = np.linalg.solve(A2, b2)
            self._phase2_func = np.poly1d(x2)
        except Exception:
            pass

        if phase_1_time > 0:
            a11 = (self._step_length/2 - self._input_position[1]) / phase_1_time
            a10 = self._input_position[1]
            self._phase1_func = np.poly1d(np.array([a11, a10]))

        self._swing_y_func = lambda x: (self._step_length / 2) * np.cos(x)
        self._swing_z_func = lambda x: self._step_height * np.sin(x)
        
    @staticmethod
    def min_max_norm(val, min_val, max_val, new_min, new_max):
        return (val - min_val) * (new_max - new_min) / (max_val - min_val) + new_min
        
    def get_position(self, t: float) -> np.ndarray:
        movement_unit = self._movement_time * self._swing_percentage
        
        if t < self._leg_nb*movement_unit:
            return np.array([self._input_position[0], self._phase1_func(t), self._input_position[2]])

        elif self._leg_nb*movement_unit <= t < (self._leg_nb+1)*movement_unit:
            t = self.min_max_norm(t, self._leg_nb*movement_unit, (self._leg_nb+1)*movement_unit, 0, np.pi)
            return np.array([self._input_position[0], self._swing_y_func(t), self._input_position[2]+self._swing_z_func(t)])
        else:
            return np.array([self._input_position[0], self._phase2_func(t), self._input_position[2]])