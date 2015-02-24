import warnings

try:
    import eval
except ImportError, e:
    msg = ''.join([str(e),'; without this you cannot perform evaluation (measurements are not affected)'])
    warnings.warn(msg, ImportWarning)

try:
    import meas
except ImportError, e:
    msg = ''.join([str(e),'; without this you cannot perform measurements (evaluation is not affected)'])
    warnings.warn(msg, ImportWarning)
