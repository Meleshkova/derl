""" Defines learner test case. """
import numpy as np
from derl.torch_test_case import TorchTestCase
import derl.summary as summary


class AlgTestCase(TorchTestCase):
  """ Generic learner test case. """
  def setUp(self):
    super().setUp()
    self.env = None
    self.alg = None
    summary.stop_recording()
    summary.should_record = lambda *args, **kwargs: False

  def assert_interactions(self, fname, ignore_keys=("state", "infos"),
                          rtol=1e-7, atol=0.):
    """ Checks that interactions have values from the file. """
    ignore_keys = set(ignore_keys) or {}
    interactions = next(self.alg.runner.run())
    with np.load(fname, allow_pickle=True) as expected:
      self.assertEqual(sorted(list(interactions.keys())),
                       sorted(list(expected.keys())))
      for key in filter(lambda k: k not in ignore_keys, expected.keys()):
        with self.subTest(key=key):
          self.assertAllClose(interactions[key], expected[key],
                              rtol=rtol, atol=atol)

  def assert_grad(self, fname, rtol=1e-7, atol=0.):
    """ Checks that the gradients are close to the values from the file. """
    interactions = next(self.alg.runner.run())
    loss = self.alg.loss(interactions)
    loss.backward()
    expected = np.load(fname)
    for i, param in enumerate(self.alg.model.parameters()):
      with self.subTest(grad_i=i):
        self.assertAllClose(param.grad, expected[f"grad_{i}"],
                            rtol=rtol, atol=atol)

  def assert_losses(self, filename, rtol=1e-6, atol=0.):
    """ Checks that loss values are close to those from the file. """
    expected = np.load(filename)
    data_iter = self.alg.runner.run()
    for i in range(expected.shape[0]):
      loss = self.alg.step(next(data_iter))
      with self.subTest(i=i):
        self.assertAllClose(loss, expected[i], rtol=rtol, atol=atol)
