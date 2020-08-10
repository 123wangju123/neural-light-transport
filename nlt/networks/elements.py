# pylint: disable=relative-beyond-top-level

import tensorflow as tf
tf.compat.v1.enable_eager_execution()

from util import logging as logutil


logger = logutil.Logger(loggee="networks/elements")


def conv(kernel_size, n_ch_out, stride=1):
    return tf.keras.layers.Conv2D(
        n_ch_out,
        kernel_size,
        strides=stride,
        padding='same')


def deconv(kernel_size, n_ch_out, stride=1):
    return tf.keras.layers.Conv2DTranspose(
        n_ch_out,
        kernel_size,
        strides=stride,
        padding='same')


def upconv(n_ch_out):
    """2x upsampling a feature map.
    """
    layers = [
        tf.keras.layers.UpSampling2D(size=2, interpolation='bilinear'),
        tf.keras.layers.Conv2D(n_ch_out, 2, padding='same')]
    return tf.keras.Sequential(layers)


def norm(type_):
    if type_ == 'batch':
        norm_layer = tf.keras.layers.BatchNormalization(
            momentum=0.99, epsilon=0.001)
    elif type_ == 'layer':
        norm_layer = tf.keras.layers.LayerNormalization(
            epsilon=0.001, center=True, scale=True)
    elif type_ == 'instance':
        norm_layer = instancenorm()
    elif type_ == 'pixel':
        norm_layer = pixelnorm()
    elif type_ is None or type_.lower() == 'none':
        norm_layer = iden()
    else:
        raise NotImplementedError(type_)
    return norm_layer


def act(type_):
    if type_ == 'relu':
        act_layer = tf.keras.layers.ReLU(negative_slope=0)
    elif type_ == 'leakyrelu':
        act_layer = tf.keras.layers.LeakyReLU(alpha=0.3)
    elif type_ == 'elu':
        act_layer = tf.keras.layers.ELU(alpha=1.0)
    else:
        raise NotImplementedError(type_)
    return act_layer


def pool(type_):
    kwargs = {
        'pool_size': 2,
        'strides': 2,
        'padding': 'same'}
    if type_ == 'max':
        pool_layer = tf.keras.layers.MaxPooling2D(**kwargs)
    elif type_ == 'avg':
        pool_layer = tf.keras.layers.AveragePooling2D(**kwargs)
    elif type_ is None or type_.lower() == 'none':
        pool_layer = iden()
    else:
        raise NotImplementedError(type_)
    return pool_layer


def instancenorm():
    return tf.keras.layers.Lambda(
        lambda x: tf.contrib.layers.instance_norm(
            x, center=True, scale=True, epsilon=1e-06))


def pixelnorm():
    def _pixelnorm(images, epsilon=1.0e-8):
        """Pixel normalization.

        For each pixel a[i,j,k] of image in HWC format, normalize its
        value to b[i,j,k] = a[i,j,k] / SQRT(SUM_k(a[i,j,k]^2) / C + eps).

        Args:
            images: A 4D `Tensor` of NHWC format.
            epsilon: A small positive number to avoid division by zero.

        Returns:
            A 4D `Tensor` with pixel-wise normalized channels.
        """
        return images * tf.rsqrt(
            tf.reduce_mean(
                tf.square(images), axis=3, keepdims=True
            ) + epsilon)
    return tf.keras.layers.Lambda(_pixelnorm)


def iden():
    return tf.keras.layers.Lambda(lambda x: x)