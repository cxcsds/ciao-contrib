
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

    def __init__(self, matrix, grid, name="matrix"):
        'Init'
        self.matrix = numpy.array(matrix)
        self.name = name
        self.full_grid = numpy.array(grid)
        self.check_parameters()
        super().__init__(name)

    def check_parameters(self):
        'Simple checks on inputs'

        dims = self.matrix.shape
        if len(dims) != 2:
            raise PSFErr("Matrix must be 2D")

        if dims[0] != dims[1]:
            raise PSFErr("Only square matrices")

        grid_dim = self.full_grid.shape
        if dims[0] != grid_dim[0]:
            raise PSFErr("Matrix size must equal data length")

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

        # pl and pr are model parameter values
        # args is x-array
        # kwargs = ??

        data_grid = args[0]

        if len(data_grid) == len(self.full_grid):
            are_equal = (data_grid == self.full_grid)
            if not are_equal.all():
                raise PSFErr("Input X-array does not match Full grid used to create MatrixModel")
        elif len(data_grid) > len(self.full_grid):
            raise PSFErr("Mismatch in data grid compared to MatrixModel grid")
        else:
            common_grid = numpy.intersect1d(data_grid, self.full_grid)
            are_equal = (common_grid == data_grid)
            if not are_equal.all():
                raise PSFErr("Data grid have values not in original grid")

        data = numpy.asarray(rhs(pr, self.full_grid, **kwargs))
        matrix = numpy.asarray(lhs(pl, self.full_grid, **kwargs))

        dshape = data.shape
        if len(dshape) != 1:
            raise PSFErr("Data must be 1D")

        mshape = matrix.shape
        if len(mshape) != 2:
            raise PSFErr("Matrix must be 2D")

        if mshape[0] != mshape[1]:
            raise PSFErr("Only square matrices")

        if mshape[0] != dshape[0]:
            raise PSFErr("Matrix size must equal data length")

        full_model = numpy.matmul(matrix, data)

        if len(self.full_grid) == len(data_grid):
            return full_model

        filter_indeces, = numpy.where([c in self.full_grid for c in data_grid])
        filtered_model = full_model[filter_indeces]
        return filtered_model

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


def test_matrix_model_class():
    'Simple test of MatrixModel'

    import sherpa.astro.ui as ui
    import numpy
    from sherpa_contrib.matrix_model import MatrixModel

    xx = numpy.arange(1, 11, 1) + 0.8675309
    yy = numpy.ones_like(xx) * numpy.pi
    ee = numpy.ones_like(xx) * 0.1

    diag = numpy.identity(len(xx))

    ui.load_arrays(1, xx, yy, ee, ui.Data1D)

    my_matrix = MatrixModel(diag, xx, name="my_matrix")
    cc = ui.const1d("cc")

    ui.set_source(my_matrix(cc))
    ui.fit()

    ui.notice(3, 7)
    ui.fit()
