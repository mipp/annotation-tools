"""Convert Deep SORT oputput file to MOT challenge format"""

from __future__ import print_function
import argparse
import ast
import sys
import csv


def open_tracking_annotation(file_name):
    dets = []
    with open(file_name) as ann_file:
        for row in ann_file:
            dets.append(
                [int(ast.literal_eval(x.strip())) for x in row.strip().split(",")]
            )
    return dets


def save_detections(detections, output_name):
    with open(output_name, "w", newline="\n") as csvfile:
        writer = csv.writer(
            csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        for row in detections:
            writer.writerow(row)


def update_detections(detections):
    for i, detection in enumerate(detections):
        detection[4] = abs(detection[4] - detection[2])
        detection[5] = abs(detection[5] - detection[3])
    return detections


def main(args):
    detections = open_tracking_annotation(args.input)
    detections = update_detections(detections)
    save_detections(detections, args.input[0:-4] + "_mot.txt")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Converts Deep SORT output file to MOT challenge format", epilog="Output: <input_filename>_mot.txt")
    ap.add_argument("input", help="Tracking results file output by Deep SORT")
    args = ap.parse_args(sys.argv[1:])
    main(args)
