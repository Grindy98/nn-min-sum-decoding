from keras import metrics
import tensorflow as tf

class BER(metrics.Metric):

  def __init__(self, name='BER', **kwargs):
    super(BER, self).__init__(name=name, **kwargs)
    self.errors = self.add_weight(name='errors', initializer='zeros', dtype='int32')
    self.totals = self.add_weight(name='totals', initializer='zeros', dtype='int32')

  def update_state(self, y_true, y_pred, sample_weight=None):
    y_true = tf.where(y_true > 0 , True, False)
    y_pred = tf.where(y_pred > 0 , True, False)

    values = tf.where(tf.math.logical_xor(y_true, y_pred), 1, 0)
    self.errors.assign_add(tf.reduce_sum(values))
    self.totals.assign_add(tf.size(values))

  def result(self):
    return tf.divide(self.errors, self.totals)

  def reset_state(self):
    self.errors.assign(0)
    self.totals.assign(0)

class FER(metrics.Metric):

  def __init__(self, name='FER', **kwargs):
    super(FER, self).__init__(name=name, **kwargs)
    self.errors = self.add_weight(name='errors', initializer='zeros', dtype='int32')
    self.totals = self.add_weight(name='totals', initializer='zeros', dtype='int32')

  def update_state(self, y_true, y_pred, sample_weight=None):
    y_true = tf.where(y_true > 0 , True, False)
    y_pred = tf.where(y_pred > 0 , True, False)

    values = tf.math.logical_xor(y_true, y_pred)
    values = tf.reduce_any(values, axis=-1)
    values = tf.where(values, 1, 0)
    self.errors.assign_add(tf.reduce_sum(values))
    self.totals.assign_add(tf.size(values))

  def result(self):
    return tf.divide(self.errors, self.totals)

  def reset_state(self):
    self.errors.assign(0)
    self.totals.assign(0)