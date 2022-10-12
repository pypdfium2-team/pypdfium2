# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import pypdfium2._pypdfium as pdfium


class PdfMatrix:
    """
    PDF transformation matrix helper class (Python).
    
    See the PDF 1.7 specification, Section 8.3.3 ("Common Transformations").
    
    Note:
        * The PDF format uses row vectors.
        * Transformations operate from the origin of the coordinate system.
    
    Attributes:
        a (float): Matrix value [0][0].
        b (float): Matrix value [0][1].
        c (float): Matrix value [1][0].
        d (float): Matrix value [1][1].
        e (float): Matrix value [2][0] (X translation).
        f (float): Matrix value [2][1] (Y translation).
    """
    
    # The effect of applying the matrix on a vector (x, y) is (ax+cy+e, bx+dy+f)
    
    def __init__(self, a=1, b=0, c=0, d=1, e=0, f=0):
        self.set(a, b, c, d, e, f)
    
    def __eq__(self, matrix):
        if type(self) is not type(matrix):
            return False
        return (self.get() == matrix.get())
    
    def __repr__(self):
        return "PdfMatrix%s" % (self.get(), )
    
    def get(self):
        """
        Get the matrix as tuple of the form (a, b, c, d, e, f).
        """
        return (self.a, self.b, self.c, self.d, self.e, self.f)
    
    def set(self, a, b, c, d, e, f):
        """
        Set the matrix values.
        """
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
    
    def copy(self):
        """
        Returns:
            An independent copy of the matrix.
        """
        return PdfMatrix(*self.get())
    
    @classmethod
    def from_pdfium(cls, fs_matrix):
        """
        Load a :class:`.PdfMatrix` from a raw :class:`FS_MATRIX` object.
        """
        return PdfMatrix(
            fs_matrix.a,
            fs_matrix.b,
            fs_matrix.c,
            fs_matrix.d,
            fs_matrix.e,
            fs_matrix.f,
        )
    
    def to_pdfium(self):
        """
        Convert the matrix to a raw :class:`FS_MATRIX` object.
        """
        return pdfium.FS_MATRIX(*self.get())
    
    def multiply(self, other):
        """
        Multiply this matrix by another :class:`.PdfMatrix`, to concatenate transformations.
        """
        # M1 x M2 (self x other)
        # (a1, b1, 0)   (a2, b2, 0)   (a1a2+b1c2,    a1b2+b1d2,    0)
        # (c1, d1, 0) x (c2, d2, 0) = (c1a2+d1c2,    c1b2+d1d2,    0)
        # (e1, f1, 1)   (e2, f2, 0)   (e1a2+f1c2+e2, e1b2+f1d2+f2, 1)
        new_matrix = (
            self.a*other.a + self.b*other.c,            # a
            self.a*other.b + self.b*other.d,            # b
            self.c*other.a + self.d*other.c,            # c
            self.c*other.b + self.d*other.d,            # d
            self.e*other.a + self.f*other.c + other.e,  # e
            self.e*other.b + self.f*other.d + other.f,  # f
        )
        self.set(*new_matrix)
    
    def translate(self, x, y):
        """
        Parameters:
            x (float): Horizontal shift (<0: left, >0: right).
            y (float): Vertical shift.
        """
        # same as self.multiply( PdfMatrix(1, 0, 0, 1, x, y) )
        self.e += x
        self.f += y
    
    def scale(self, x, y):
        """
        Parameters:
            x (float): A factor to scale the X axis (<1: compress, >1: stretch).
            y (float): A factor to scale the Y axis.
        """
        # same as a*=x, b*=y, c*=x, d*=y, e*=x, f*=y
        self.multiply( PdfMatrix(x, 0, 0, y) )
    
    def rotate(self, angle):
        """
        Parameters:
            angle (float): Clockwise angle in degrees to rotate the matrix.
        """
        # row vectors -> b = -s leads to clockwise rotation indeed
        angle = (angle/180) * math.pi  # arc measure
        c, s = math.cos(angle), math.sin(angle)
        self.multiply( PdfMatrix(c, -s, s, c) )
    
    def mirror(self, vertical, horizontal):
        """
        Parameters:
            vertical (bool): Whether to mirror at the Y axis.
            horizontal (bool): Whether to mirror at the X axis.
        """
        s_x = (-1 if vertical else 1)
        s_y = (-1 if horizontal else 1)
        self.scale(s_x, s_y)
    
    def skew(self, x_angle, y_angle):
        """
        Parameters:
            x_angle (float): Inner angle in degrees to skew the X axis.
            y_angle (float): Inner angle in degrees to skew the Y axis.
        """
        tan_a = math.tan((x_angle/180) * math.pi)
        tan_b = math.tan((y_angle/180) * math.pi)
        self.multiply( PdfMatrix(1, tan_a, tan_b, 1) )
