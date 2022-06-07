# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause


def pagetext_type(value):
    
    if not value:
        return
    
    page_indices = []
    splitted = value.split(",")
    
    for page_or_range in splitted:
        
        if "-" in page_or_range:
            
            start, end = page_or_range.split("-")
            start = int(start) - 1
            end = int(end) - 1
            
            if start < end:
                pages = [i for i in range(start, end+1)]
            else:
                pages = [i for i in range(start, end-1, -1)]
            
            page_indices.extend(pages)
        
        else:
            
            page_indices.append(int(page_or_range) - 1)
    
    return page_indices
