
'A convolution model that does a matrix multiplication'


import numpy

from sherpa.models import ArithmeticConstantModel, Model, CompositeModel
from sherpa.instrument import ConvolutionModel
from sherpa.utils.err import PSFErr
import sherpa

class MatrixValue(ArithmeticConstantModel, Model):
    '''
    Need to wrap the matrix as a type of model, and looks like
    a ConstantModel is closest.

    But ArithmeticConstantModel restricts the value to a 1D array;
    we need to remove that restriction which is done in this subclass.
    '''

    def _set_val(self, val):
        'Set the matrix value'
        self._val = val

    def _get_val(self):
        'Get the matrix value'
        return self._val

    def __init__(self,
                 val,
                 name=None):
        'Init routine'
        self.name = name or 'matrix'
        self.val = val
        self.ndim = None

        Model.__init__(self, self.name)

    val = property(_get_val, _set_val,
                   doc='The matrix constant.')

    # ~ def get_center(self):
        # ~ 'defined in abc'
        # ~ return

    # ~ def guess(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return

    # ~ def set_center(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return


class MatrixConvolution(ConvolutionModel, CompositeModel):
    'Define the return type of the MatrixModel'

    def __init__(self, lhs, rhs, psf):
        'Need separate init '

        # wrapkern/whatever us isinstance instead of issubclass
        self.lhs = lhs

        self.rhs = self.wrapobj(rhs)

        # Need self.psf.calc() is called
        self.psf = psf

        CompositeModel.__init__(self,
                                f"matrix.{self.psf.name}({self.rhs.name})",
                                (self.psf, self.lhs, self.rhs))

    # ~ def get_center(self):
        # ~ 'defined in abc'
        # ~ return

    # ~ def guess(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return

    # ~ def set_center(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return


class MatrixModel(Model):
    'Implements a convolution that is a matrix multiplication'

    string_types = (str, )

    def __init__(self, matrix, name="matrix"):
        'Init'
        self.matrix = matrix
        self.name = name
        super().__init__(name)

    def __repr__(self):
        'what am I'
        return f"<{type(self).__name__} matrix instance>"

    def __str__(self):
        'string versin of what am I'
        if self.matrix is None:
            raise PSFErr('notset')

        return f"Convolution Matrix:\n{self.name}"

    def __call__(self, model, session=None):
        'Make the object callable'

        if isinstance(model, self.string_types):
            if session is None:
                model = sherpa.astro.ui._session._eval_model_expression(model)
            else:
                model = session._eval_model_expression(model)

        return MatrixConvolution(MatrixValue(self.matrix), model, self)

    def calc(self, pl, pr, lhs, rhs, *args, **kwargs):
        'Perform the matrix multiplication'

        data = numpy.asarray(rhs(pr, *args, **kwargs))
        matrix = numpy.asarray(lhs(pl, *args, **kwargs))

        dshape = data.shape
        if len(dshape) != 1:
            raise PSFErr("Data must be 1D")

        mshape = matrix.shape
        if len(mshape) != 2:
            raise PSFErr("Matrix must be 2D")

        if mshape[0] != mshape[1]:
            raise PSFErr("Only square matrixes")

        if mshape[0] != dshape[0]:
            raise PSFErr("Matrix size must equal data length")

        return numpy.matmul(matrix, data)

    # ~ def get_center(self):
        # ~ 'defined in abc'
        # ~ return

    # ~ def guess(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return

    # ~ def set_center(self, *args, **kwargs):
        # ~ 'defined in abc'
        # ~ return

    # ~ def startup(self):
        # ~ 'defined in abc'
        # ~ return

    # ~ def teardown(self):
        # ~ 'defined in abc'
        # ~ return
