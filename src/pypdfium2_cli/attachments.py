# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pathlib import Path
from pypdfium2_cli._parsers import (
    add_input, get_input,
    parse_numtext,
)

ACTION_LIST    = "list"
ACTION_EXTRACT = "extract"
ACTION_EDIT    = "edit"

# TODO would like to add action="extend", but conflicts with default being a tuple, and beware: it cannot be made a list here (perilous!)
NARGS_PLUS = dict(nargs="+", default=())

def attach(parser):  # hook
    
    add_input(parser, pages=False)
    subparsers = parser.add_subparsers(dest="action")  # required=True  # >= 3.7
    
    subparsers.add_parser(ACTION_LIST)
    
    parser_extract = subparsers.add_parser(ACTION_EXTRACT)
    parser_extract.add_argument(
        "--nums",
        type = parse_numtext,
    )
    parser_extract.add_argument(
        "--output-dir", "-o",
        type = Path,
        required = True,
    )
    
    parser_edit = subparsers.add_parser(ACTION_EDIT)
    parser_edit.add_argument(
        "--set-desc",
        **NARGS_PLUS,
        help = f"Syntax: n=desc, where n is the attachment number, and desc the new description to be set. Example: '1=Hello world'. Use `pypdfium2 attachments list` to determine the attachment numbers.",
    )
    parser_edit.add_argument(
        "--del-nums",
        type = parse_numtext,
        default = (),
    )
    # TODO need a way to set the name and description of new attachments
    parser_edit.add_argument(
        "--add-files",
        **NARGS_PLUS,
        metavar = "F",
        type = Path,
    )
    parser_edit.add_argument(
        "--output", "-o",
        type = Path,
        required = True,
    )


def main(args):
    
    pdf = get_input(args)
    n_attachments = pdf.count_attachments()
    
    if args.action == ACTION_LIST:
        for i in range(n_attachments):
            attachment = pdf.get_attachment(i)
            print(f"[{i+1}] {attachment.get_name()}: {attachment.get_desc()}")
    
    elif args.action == ACTION_EXTRACT:
        
        if not args.nums:
            args.nums = range(n_attachments)
        n_digits = len(str( max(args.nums) + 1 ))
        
        for i in args.nums:
            attachment = pdf.get_attachment(i)
            name = attachment.get_name()
            out_path = args.output_dir / ("%0*d_%s" % (n_digits, i+1, name))
            out_path.write_bytes( attachment.get_data() )
    
    elif args.action == ACTION_EDIT:
        
        for spec in args.set_desc:
            num_str, desc = spec.split("=", maxsplit=1)
            i = int(num_str) - 1
            attachment = pdf.get_attachment(i)
            attachment.set_desc(desc)
        
        for i in sorted(args.del_nums, reverse=True):
            pdf.del_attachment(i)
        
        for fp in args.add_files:
            attachment = pdf.new_attachment(fp.name)
            attachment.set_data( fp.read_bytes() )
        
        pdf.save(args.output)
    
    else:
        raise ValueError("No valid subcommand provided")
