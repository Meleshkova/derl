"""
Defines base classes.
"""
from abc import ABC, abstractmethod
import re

import tensorflow as tf
from .train import StepVariable


class BaseRunner(ABC):
  """ General data runner. """
  def __init__(self, env, policy, step_var=None):
    self.env = env
    self.policy = policy
    if step_var is None:
      step_var = StepVariable(f"{camel2snake(self.__class__.__name__)}_step",
                              tf.train.create_global_step())
    self.step_var = step_var

  @property
  def nenvs(self):
    """ Returns number of batched envs or `None` if env is not batched """
    return getattr(self.env.unwrapped, "nenvs", None)

  @abstractmethod
  def get_next(self):
    """ Returns next data object """


def camel2snake(name):
  """ Converts camel case to snake case. """
  sub = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', sub).lower()


class BaseAlgorithm(ABC):
  """ Base algorithm. """
  def __init__(self, model, optimizer=None, step_var=None):
    self.model = model
    self.optimizer = optimizer or self.model.optimizer
    if step_var is None:
      step_var = StepVariable(f"{camel2snake(self.__class__.__name__)}_step")
    self.step_var = step_var

  @abstractmethod
  def loss(self, data):
    """ Computes the loss given inputs and target values. """

  def preprocess_gradients(self, gradients):
    """ Applies gradient preprocessing. """
    # pylint: disable=no-self-use
    return gradients

  def step(self, data):
    """ Performs single training step of the algorithm. """
    with tf.GradientTape() as tape:
      loss = self.loss(data)
    gradients = self.preprocess_gradients(
        tape.gradient(loss, self.model.trainable_variables))
    self.optimizer.apply_gradients(zip(gradients,
                                       self.model.trainable_variables))
    if getattr(self.step_var, "auto_update", True):
      self.step_var.assign_add(1)
    return loss
