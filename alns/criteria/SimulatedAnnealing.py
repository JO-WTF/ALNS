import numpy as np
import matplotlib.pyplot as plt
from .AcceptanceCriterion import AcceptanceCriterion
from .update import update


class SimulatedAnnealing(AcceptanceCriterion):

    def __init__(self, start_temperature, end_temperature, step,
                 method="linear"):
        """
        Simulated annealing, using an updating temperature. The temperature is
        updated as,
        ``temperature = max(end_temperature, temperature - step)`` (linear)
        ``temperature = max(end_temperature, step * temperature)`` (exponential)
        where the initial temperature is set to ``start_temperature``.
        Parameters
        ----------
        start_temperature : float
            The initial temperature.
        end_temperature : float
            The final temperature.
        step : float
            The updating step.
        method : str
            The updating method, one of {'linear', 'exponential'}. Default
            'linear'.
        References
        ----------
        - Santini, A., Ropke, S. & Hvattum, L.M. A comparison of acceptance
          criteria for the adaptive large neighbourhood search metaheuristic.
          *Journal of Heuristics* (2018) 24 (5): 783–815.
        - Kirkpatrick, S., Gerlatt, C. D. Jr., and Vecchi, M. P. Optimization
          by Simulated Annealing. *IBM Research Report* RC 9355, 1982.
        """
        if start_temperature <= 0 or end_temperature <= 0 or step < 0:
            raise ValueError("Temperatures must be strictly positive.")

        if start_temperature < end_temperature:
            raise ValueError("Start temperature must be bigger than end "
                             "temperature.")

        if method == "exponential" and step > 1:
            raise ValueError("For exponential updating, the step parameter "
                             "must not be explosive.")

        self._start_temperature = start_temperature
        self._end_temperature = end_temperature
        self._step = step
        self._method = method

        self._temperature = start_temperature
        self._temperatures = []
        self._temperatures.append(start_temperature)
        self._probs = []
        self._acceptState = []

    @property
    def start_temperature(self):
        return self._start_temperature

    @property
    def end_temperature(self):
        return self._end_temperature

    @property
    def step(self):
        return self._step

    @property
    def method(self):
        return self._method
    
    def plotAnalytics(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        x = range(len(self._temperatures))
        y = self._temperatures
        ax.set_title("Temperature cooldown over time")
        plt.scatter(x, y)
        plt.draw_if_interactive()

        fig, ax = plt.subplots(figsize=(10, 10))
        x = range(len(self._probs))
        y = self._probs
        ax.set_title("Acceptance probability over time")
        plt.scatter(x, y)
        plt.ylim(0, 5)
        plt.draw_if_interactive()

        fig, ax = plt.subplots(figsize=(10, 10))
        x = range(len(self._acceptState))
        y = self._acceptState
        plt.ylim(0, 1.1)
        ax.set_title("Truth states over time")
        plt.plot(x, y)
        plt.draw_if_interactive()

    def accept(self, rnd, best, current, candidate):
        probability = np.exp((current.objective() - candidate.objective())
                             / self._temperature)

        self._probs.append(probability)

        # We should not set a temperature that is lower than the end
        # temperature.
        self._temperature = max(self.end_temperature, update(self._temperature,
                                                             self.step,
                                                             self.method))

        self._temperatures.append(self._temperature)

        # TODO deprecate RandomState in favour of Generator - which uses
        #  random(), rather than random_sample().
        try:
            res = probability >= rnd.random()
            self._acceptState.append(res)
            return res
        except AttributeError:
            res = probability >= rnd.random_sample()
            self._acceptState.append(res)
            return res