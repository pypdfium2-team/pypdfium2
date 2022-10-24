# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause


def parse_pagetext(pagetext):
    
    if not pagetext:
        return None
    indices = []
    
    for page_or_range in pagetext.split(","):
        if "-" in page_or_range:
            start, end = page_or_range.split("-")
            start = int(start) - 1
            end   = int(end)   - 1
            if start < end:
                indices.extend( [i for i in range(start, end+1)] )
            else:
                indices.extend( [i for i in range(start, end-1, -1)] )
        else:
            indices.append(int(page_or_range) - 1)
    
    return indices
