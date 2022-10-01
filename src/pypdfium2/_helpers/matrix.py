# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO

class PdfMatrix:
    
    def __init__(self):
        pass
    
    def get(self):
        """
        Get the matrix as tuple of the form (a, b, c, d, e, f).
        """
        pass
    
    @classmethod
    def from_pdfium(self, fs_matrix):
        """
        Load a :class:`.PdfMatrix` from an :class:`FS_MATRIX`.
        """
        pass
    
    def to_pdfium(self):
        """
        Convert the matrix to an :class:`FS_MATRIX`.
        """
        pass
    
    def multiply(self, matrix):
        """
        Multiply this matrix by another matrix, to concatenate transformations.
        """
        pass
    
    def translate(self, x, y):
        """
        Parameters:
            x (int|float): Horizontal shift (negative: left, positive: right).
            y (int|float): Vertical shift (negative: left, positive: right).
        """
        pass
    
    def scale(self, x, y):
        """
        Parameters:
            x (int|float): A factor to compress or stretch the X axis.
            y (int|float): A factor to compress or stretch the Y axis.
        """
        pass
    
    def rotate(self, angle):
        """
        Parameters:
            angle (int|float): Clockwise angle in degrees to rotate the matrix.
        """
        pass
    
    def mirror(self, x, y):
        """
        Parameters:
            x (bool): Whether to flip the X axis.
            y (bool): Whether to flip the Y axis.
        """
        pass
    
    def skew(self, x_angle, y_angle):
        """
        Parameters:
            x_angle (int|float): Angle in degrees to skew the X axis.
            y_angle (int|float): Angle in degrees to skew the Y axis.
        """
        pass
