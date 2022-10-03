# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium


class PdfMatrix:
    """
    PDF transformation matrix helper class.
    See the PDF 1.7 specification, Section 8.3.3 ("Common Transformations").
    """
    
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
        Get the matrix as tuple of the form (a, b, c, d, e, f).
        """
        return (self.a, self.b, self.c, self.d, self.e, self.f)
    
    @classmethod
    def from_pdfium(cls, fs_matrix):
        """
        Load a :class:`.PdfMatrix` from a raw :class:`FS_MATRIX` object.
        """
        values = {char: getattr(fs_matrix, char) for char in "abcdef"}
        return cls(**values)
    
    def to_pdfium(self):
        """
        Convert the matrix to a raw :class:`FS_MATRIX` object.
        """
        fs_matrix = pdfium.FS_MATRIX()
        for char in "abcdef":
            setattr(fs_matrix, char, getattr(self, char))
        return fs_matrix
