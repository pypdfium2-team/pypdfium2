# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import pypdfium2._pypdfium as pdfium


class PdfMatrix:
    
    def __init__(self, a=1, b=0, c=0, d=1, e=0, f=0):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
    
    def __eq__(self, matrix):
        if type(self) is not type(matrix):
            return False
        return (self.get() == matrix.get())
    
    def get(self):
        """
        Get the matrix as list of the form (a, b, c, d, e, f).
        """
        return [self.a, self.b, self.c, self.d, self.e, self.f]
    
    @classmethod
    def from_pdfium(cls, fs_matrix):
        """
        Load a :class:`.PdfMatrix` from an :class:`FS_MATRIX`.
        """
        values = {char: getattr(fs_matrix, char) for char in "abcdef"}
        return cls(**values)
    
    def to_pdfium(self):
        """
        Convert the matrix to an :class:`FS_MATRIX`.
        """
        fs_matrix = pdfium.FS_MATRIX()
        for char in "abcdef":
            setattr(fs_matrix, char, getattr(self, char))
        return fs_matrix
    
    def multiply(self, matrix):
        """
        Multiply this matrix by another :class:`.PdfMatrix`, to concatenate transformations.
        """
        new_matrix = dict(
            a = self.a*matrix.a + self.b*matrix.c,
            b = self.a*matrix.b + self.b*matrix.d,
            c = self.c*matrix.a + self.d*matrix.c,
            d = self.c*matrix.b + self.d*matrix.d,
        )
        for char, value in new_matrix.items():
            setattr(self, char, value)
    
    def translate(self, x, y):
        """
        Parameters:
            x (int|float): Horizontal shift (negative: left, positive: right).
            y (int|float): Vertical shift (negative: left, positive: right).
        """
        self.e += x
        self.f += y
    
    def scale(self, x, y):
        """
        Parameters:
            x (int|float): A factor to compress or stretch the X axis.
            y (int|float): A factor to compress or stretch the Y axis.
        """
        self.multiply( PdfMatrix(x, 0, 0, y) )
    
    def rotate(self, angle):
        """
        Parameters:
            angle (int|float): Clockwise angle in degrees to rotate the matrix
        """
        angle = (angle/180) * math.pi
        c, s = math.cos(angle), math.sin(angle)
        self.multiply( PdfMatrix(c, -s, s, c) )
    
    def mirror(self, x, y):
        """
        Parameters:
            x (bool): Whether to flip the X axis.
            y (bool): Whether to flip the Y axis.
        """
        s_x = (-1 if x else 1)
        s_y = (-1 if y else 1)
        self.scale(s_x, s_y)
    
    def skew(self, x_angle, y_angle):
        """
        Parameters:
            x_angle (int|float): Angle in degrees to skew the X axis.
            y_angle (int|float): Angle in degrees to skew the Y axis.
        """
        tan_a = math.tan((x_angle/180) * math.pi)
        tan_b = math.tan((y_angle/180) * math.pi)
        self.multiply( PdfMatrix(1, tan_a, tan_b, 1) )
