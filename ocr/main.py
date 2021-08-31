#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import shutil
import os
from os.path import join
import logging

from .input import pdftotext, tesseract5
from .input import pdfminer_wrapper
from .input import tesseract
from .input import tesseract4
from .input import gvision

from .extract.loader import read_templates

from .output import to_csv
from .output import to_json
from .output import to_xml
import spacy

logger = logging.getLogger(__name__)

input_mapping = {
    "pdftotext": pdftotext,
    "tesseract": tesseract,
    "tesseract4": tesseract4,
    "pdfminer": pdfminer_wrapper,
    "gvision": gvision,
    "tesseract5": tesseract5
}

output_mapping = {"csv": to_csv, "json": to_json, "xml": to_xml, "none": None}


def extract_data(invoicefile, templates=None, input_module=pdftotext):
    """Extracts structured data from PDF/image invoices.

    This function uses the text extracted from a PDF file or image and
    pre-defined regex templates to find structured data.

    Reads template if no template assigned
    Required fields are matches from templates

    Parameters
    ----------
    invoicefile : str
        path of electronic invoice file in PDF,JPEG,PNG (example: "/home/duskybomb/pdf/invoice.pdf")
    templates : list of instances of class `InvoiceTemplate`, optional
        Templates are loaded using `read_template` function in `loader.py`
    input_module : {'pdftotext', 'pdfminer', 'tesseract'}, optional
        library to be used to extract text from given `invoicefile`,

    Returns
    -------
    dict or False
        extracted and matched fields or False if no template matches

    Notes
    -----
    Import required `input_module` when using invoice2data as a library

    See Also
    --------
    read_template : Function where templates are loaded
    InvoiceTemplate : Class representing single template files that live as .yml files on the disk

    Examples
    --------
    When using `invoice2data` as an library

    >>> from invoice2data.input import pdftotext
    >>> extract_data("invoice2data/test/pdfs/oyo.pdf", None, pdftotext)
    {'issuer': 'OYO', 'amount': 1939.0, 'date': datetime.datetime(2017, 12, 31, 0, 0), 'invoice_number': 'IBZY2087',
     'currency': 'INR', 'desc': 'Invoice IBZY2087 from OYO'}

    """
    if templates is None:
        templates = read_templates()

    # print(templates[0])
    extracted_str = input_module.to_text(invoicefile).decode("utf-8")

    # print("extracted_str:", extracted_str)
    def regex_model():
        logger.debug("START pdftotext result ===========================")
        logger.debug(extracted_str)
        logger.debug("END pdftotext result =============================")

        logger.debug("Testing {} template files".format(len(templates)))
        for t in templates:
            optimized_str = t.prepare_input(extracted_str)
            print("optimized_str:", extracted_str)

            if t.matches_input(optimized_str):
                identified_fields = t.extract(optimized_str)
                print("identified_fields:", identified_fields)
                if not is_all_fields_empty(identified_fields):
                    print(identified_fields)
                    return identified_fields

        logger.error("No template for %s", invoicefile)
        return False

    def spacy_model():
        final_dict = {}
        f = open("output.txt", "w+")
        f.write(extracted_str)
        f.close()

        f1 = open("optimized.txt", "w+")
        with open("output.txt") as f:
            for line in f:
                print(line)
                if not line.isspace():
                    f1.write(line)

        f1.close()
        file = open("optimized.txt", "r")
        text = file.read()
        file.close()
        nlp = spacy.load("./model483")
        list_lines = text.splitlines()

        l_of_lines = []
        for i, line in enumerate(list_lines):
            doc = nlp(line)
            l_of_lines.append([(ent.text, ent.label_) for ent in doc.ents])

        doc = nlp(text)
        l_of_text = [(ent.text, ent.label_) for ent in doc.ents]

        for i in l_of_text:
            if i[1] == "UDYAM REGISTRATION NUMBER":
                if len(i[0]) >= 10:
                    final_dict[i[1]] = i[0]
            elif i[1] == "UDYOG AADHAR NUMBER":
                if len(i[0]) >= 10:
                    final_dict[i[1]] = i[0]
            else:
                final_dict[i[1]] = i[0]

        for i in l_of_lines:
            if len(i) > 0:
                for j in range(len(i)):
                    if i[j][1] == "UDYAM REGISTRATION NUMBER":
                        if len(i[j][0]) >= 10:
                            final_dict[i[j][1]] = i[j][0]
                    elif i[j][1] == "UDYOG AADHAR NUMBER":
                        if len(i[j][0]) >= 10:
                            final_dict[i[j][1]] = i[j][0]
                    elif i[j][1] == "NAME OF ENTERPRISE":
                        if (len(i[j][0]) > 2):
                            final_dict[i[j][1]] = i[j][0]
                    else:
                        final_dict[i[j][1]] = i[j][0]

        print("line by line", l_of_lines)
        print("\n ---------------")
        print("doc", l_of_text)
        return final_dict

    reg_dict = regex_model()
    spacy_dict = spacy_model()
    print("regex_dict", reg_dict)
    print("-----------------")
    print("spacy_dict", spacy_dict)
    final = {}
    if reg_dict != False:
        for key, val in reg_dict.items():
            if val != "[]":
                final[key] = val

    for key, val in spacy_dict.items():
        if key not in final.keys():
            final[key] = val

    return final


# check if all other fields apart from issuer are empty
def is_all_fields_empty(identified_fields):
    for key, value in identified_fields.items():
        if key != "issuer":
            if value:
                return False
    return True


def create_parser():
    """Returns argument parser """

    parser = argparse.ArgumentParser(
        description="Extract structured data from PDF files and save to CSV or JSON."
    )

    parser.add_argument(
        "--input-reader",
        choices=input_mapping.keys(),
        default="pdftotext",
        help="Choose text extraction function. Default: pdftotext",
    )

    parser.add_argument(
        "--output-format",
        choices=output_mapping.keys(),
        default="none",
        help="Choose output format. Default: none",
    )

    parser.add_argument(
        "--output-date-format",
        dest="output_date_format",
        default="%Y-%m-%d",
        help="Choose output date format. Default: %%Y-%%m-%%d (ISO 8601 Date)",
    )

    parser.add_argument(
        "--output-name",
        "-o",
        dest="output_name",
        default="invoices-output",
        help="Custom name for output file. Extension is added based on chosen format.",
    )

    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Enable debug information."
    )

    parser.add_argument(
        "--copy",
        "-c",
        dest="copy",
        help="Copy and rename processed PDFs to specified folder.",
    )

    parser.add_argument(
        "--move",
        "-m",
        dest="move",
        help="Move and rename processed PDFs to specified folder.",
    )

    parser.add_argument(
        "--filename-format",
        dest="filename",
        default="{date} {invoice_number} {desc}.pdf",
        help="Filename format to use when moving or copying processed PDFs."
             'Default: "{date} {invoice_number} {desc}.pdf"',
    )

    parser.add_argument(
        "--template-folder",
        "-t",
        dest="template_folder",
        help="Folder containing invoice templates in yml file. Always adds built-in templates.",
    )

    parser.add_argument(
        "--exclude-built-in-templates",
        dest="exclude_built_in_templates",
        default=False,
        help="Ignore built-in templates.",
        action="store_true",
    )

    parser.add_argument(
        "input_files",
        type=argparse.FileType("r"),
        nargs="+",
        help="File or directory to analyze.",
    )

    return parser


def main(args=None):
    """Take folder or single file and analyze each."""
    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    input_module = input_mapping[args.input_reader]
    output_module = output_mapping[args.output_format]

    templates = []
    # Load templates from external folder if set.
    if args.template_folder:
        templates += read_templates(os.path.abspath(args.template_folder))

    # Load internal templates, if not disabled.
    if not args.exclude_built_in_templates:
        templates += read_templates()
    output = []
    for f in args.input_files:
        res = extract_data(f.name, templates=templates, input_module=input_module)
        if res:
            logger.info(res)
            output.append(res)
            if args.copy:
                filename = args.filename.format(
                    date=res["date"].strftime("%Y-%m-%d"),
                    invoice_number=res["invoice_number"],
                    desc=res["desc"],
                )
                shutil.copyfile(f.name, join(args.copy, filename))
            if args.move:
                filename = args.filename.format(
                    date=res["date"].strftime("%Y-%m-%d"),
                    invoice_number=res["invoice_number"],
                    desc=res["desc"],
                )
                shutil.move(f.name, join(args.move, filename))
        f.close()

    if output_module is not None:
        output_module.write_to_file(output, args.output_name, args.output_date_format)


if __name__ == "__main__":
    main()
