"""Interactively edit object annotations


Keys: 
o/p : previous/next image
k/l: previous/next class label
n: new bounding box
backspace: delete selected bounding box
Esc: exit program.

Mouse:
When no box is selected:
Left click within bounding box: select bounding box.
When a box is selected:
Redraw a new box by left clicking two opposite corners of desired bouding box.
When drawing new box (keyboard n was pressed):
Draw a new box by left clicking two opposite corners of desired bouding box.

Right click within selected bounding box: Edit ID of clicked box. Enter new id and press ENTER. Edited box is shown with orange border.
Right click within another bounding box: swap IDs of clicked box with previously selected box.

Edited annotations are automatically saved in directory given by --output parameter.

"""
import argparse
import ast
import os
import platform
import sys
from collections import defaultdict

import cv2


if platform.system() == "Windows":
    import win32api  # noqa

    screen_x = win32api.GetSystemMetrics(0)
    screen_y = win32api.GetSystemMetrics(1)
elif platform.system() == "Linux":
    screen_x = 2560
    screen_y = 1440
elif platform.system() == "Darwin":
    screen_x = 1024
    screen_y = 768
else:
    screen_x = 1024
    screen_y = 768

ix, iy = -1, -1
drawing = False  # true if mouse is pressed
klasa = 0  # Klasa za nove anotacije
selected = None
update_display = True
save = False


def box2yolo(box, img_shape):
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = (box[0] + box[2]) / 2.0
    y = (box[1] + box[3]) / 2.0

    x = x / img_shape[1]
    w = w * 1.0 / img_shape[1]
    y = y / img_shape[0]
    h = h * 1.0 / img_shape[0]
    return box[4], x, y, w, h


def yolo2cv(res, img_shape):
    w = img_shape[1]
    h = img_shape[0]
    center_x = res[1] * w
    center_y = res[2] * h
    width = int(res[3] * w)
    height = int(res[4] * h)
    ul_x = int(center_x - width / 2)  # Upper Left corner X coord
    ul_y = int(center_y - height / 2)  # Upper left Y
    lr_x = ul_x + width
    lr_y = ul_y + height
    return ul_x, ul_y, lr_x, lr_y, res[0]


def open_yolo_annotation(file_name):
    dets = []
    with open(file_name) as ann_file:
        for row in ann_file:
            dets.append([ast.literal_eval(x) for x in row.strip().split(" ")])
    return dets


def put_annotations(img, boxes, names):
    box_colors = {0: (0, 200, 0), 1: (0, 0, 200), 7: (200, 0, 200)}
    font = cv2.FONT_HERSHEY_SIMPLEX
    for box in boxes:
        try:
            cv2.rectangle(img, box[0:2], box[2:4], box_colors[box[4]], 2)
        except:
            cv2.rectangle(img, box[0:2], box[2:4], box_colors[7], 2)
        if names is not None:
            tk = names[box[4]]
        else:
            tk = box[4]
        cv2.putText(img, tk, (int(box[0]), int(box[1])), font, 0.8, (0, 200, 0), 2, cv2.LINE_AA)
    if names is not None:
        cv2.putText(img, names[klasa], (10, 15), font, 0.8, (0, 200, 0), 2, cv2.LINE_AA)
    else:
        cv2.putText(img, str(klasa), (10, 15), font, 0.8, (0, 200, 0), 2, cv2.LINE_AA)
    return img


def rescale_screen(im):
    dx = screen_x - im.shape[1]
    dy = screen_y - im.shape[0]
    sr = screen_x / float(screen_y)
    ir = im.shape[1] / float(im.shape[0])
    if dx >= 0 and dy >= 0:
        return im
    elif ir > sr:
        m = float(screen_x) / im.shape[1]
    else:
        m = im.shape[0] / float(screen_y)
    im = cv2.resize(im, dsize=None, fx=m, fy=m)
    return im

def main(args):
    global klasa, update_display, selected, save, drawing
    # Annotate single image:
    if args.image is not None:
        image_fnames = [args.image]
        OUTPUT_PATH = os.path.join(os.path.dirname(args.image), "anotacije")
    # If yolo data config is provided, get class names and create new train list 
    # with new annotations
    if args.data is not None:
        yolodata = {}
        try:
            with open(args.data) as dfile:
                for line in dfile:
                    k, v = line.split('=')
                    yolodata[k.strip()] = v.strip()
        except:
            print("Error reading yolo data config file", args.data)
    # For auto-labeling:
    if args.cfg is not None and args.weights is not None:
        # TODO: implement
        pass
        
    elif os.path.exists(args.img_dir):
        image_fnames = sorted(
            [
                os.path.join(args.img_dir, x)
                for x in os.listdir(args.img_dir)
                if x.endswith(".jpg") or x.endswith('.bmp')
            ]
        )
        if args.output is not None:
            OUTPUT_PATH = args.output
        else:
            OUTPUT_PATH = os.path.join(args.txt_dir, "anotacije")
    else:
        print("Direktorij ne sadrži anotacije")
        sys.exit(0)

    if args.names is not None:
        names = [line.rstrip() for line in open(args.names, 'r')]
        br_klasa = len(names)
    else:
        try:
            names = [line.rstrip() for line in open(yolodata["names"], 'r')]
            br_klasa = int(yolodata["classes"])
        except:
            names = None
            br_klasa = 2
        
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    img_idx = 0
    while 0 <= img_idx < len(image_fnames):
        image_fname = image_fnames[img_idx]
        im = cv2.imread(image_fname)
        im = rescale_screen(im)
        cv2.namedWindow("image")
        cv2.setWindowTitle("image", image_fname)
        img = im.copy()
        try:
            x = os.path.join(
                    OUTPUT_PATH, os.path.splitext(os.path.basename(image_fname))[0] + '.txt'
                )
            resy = open_yolo_annotation(
                os.path.join(
                    OUTPUT_PATH, os.path.splitext(os.path.basename(image_fname))[0] + '.txt'
                )
            )
        except:
            try:
                resy = open_yolo_annotation(
                    os.path.join(
                        args.txt_dir,
                        os.path.splitext(os.path.basename(image_fname))[0] + '.txt'
                    )
                )
            except:
                resy = []
        boxes = [yolo2cv(r, img.shape) for r in resy]
        cv2.setMouseCallback("image", probe_position, param=[boxes, img, im])

        while 1:
            if update_display:
                img = im.copy()
                img = put_annotations(img, boxes, names)
                if selected is not None:
                    box = boxes[selected]
                    cv2.rectangle(img, box[0:2], box[2:4], (255, 255, 255), 2)
                cv2.imshow("image", img)
                update_display = False
            if save:
                print(
                    os.path.join(
                        OUTPUT_PATH, os.path.splitext(os.path.basename(image_fname))[0] + '.txt'
                    )
                )
                with open(
                    os.path.join(
                        OUTPUT_PATH, os.path.splitext(os.path.basename(image_fname))[0] + '.txt'
                    ),
                    "w",
                ) as f:
                    for box in boxes:
                        print("%d %2f %2f %2f %2f" % box2yolo(box, img.shape), file=f)
                save = False
            k = cv2.waitKey(1) & 0xFF
            if k == ord("k"):  # Prethodna aktivna klasa
                klasa -= 1
                if klasa < 0:
                    klasa = br_klasa - 1
                update_display = True
                # print("Odabrana je klasa {0}".format(klasa))
            elif k == ord("l"):  # Sljedeća aktivna klasa
                klasa += 1
                if klasa > br_klasa - 1:
                    klasa = 0
                update_display = True
                # print("Odabrana je klasa {0}".format(klasa))
            # elif k == ord('s'):  # Save
            #     with open(os.path.join(OUTPUT_PATH, image_fname.split('/')[-1][:-3]+'novo.txt'), 'w') as f:
            #         for box in boxes:
            #             print('%d %2f %2f %2f %2f'% box2yolo(box, img.shape), file=f)
            # elif k == ord('r'):  # Revert
            #     #with open(os.path.join(OUTPUT_PATH, image_fname.split('/')[-1][:-3]+'txt'), 'w') as f:
            #     print("Originalna anotacija:")
            #     for box in resy:
            #         print(box)
            elif k == ord("n"):  # New
                if not drawing:
                    selected = len(boxes)
                    boxes.append((0, 0, 0, 0, klasa))
            elif k == 8: 
                if selected is not None:
                    del boxes[selected]
                    selected = None
                    save = True
                    update_display = True
            elif k == ord("o") or k == ord("b"):
                if img_idx > 0:
                    img_idx -= 1
                drawing = False
                selected = None
                update_display = True
                break
            elif k == ord("p") or k == ord("m"):
                img_idx += 1
                drawing = False
                selected = None
                update_display = True
                break
            elif k == 27:
                cv2.destroyAllWindows()
                sys.exit(0)
        update_display = True
    cv2.destroyAllWindows()


def within(point, box):
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def probe_position(event, x, y, flags, param):
    global ix, iy, drawing, save, selected, update_display
    boxes = param[0]
    if event == cv2.EVENT_LBUTTONDOWN:
        if selected is None:
            for i in range(len(boxes)):
                if within((x, y), boxes[i]):
                    print("Within box {}".format(i))
                    selected = i
                    update_display = True
        else:
            drawing = True
            ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img = param[2].copy()
            cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 1)
            cv2.imshow("image", img)
    elif event == cv2.EVENT_LBUTTONUP:
        if drawing:
            boxes[selected] = (
                min(ix, x),
                min(iy, y),
                max(ix, x),
                max(iy, y),
                boxes[selected][4],
            )
            selected = None
            drawing = False
            save = True
            update_display = True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Image annotation tool.")
    ap.add_argument("--image", help="image to annotate")
    ap.add_argument("--img_dir", help="directory contatining images to annotate", default="jpgs")
    ap.add_argument("--txt_dir", help="existing annotations directory")
    ap.add_argument("--names", help="class names file (each class in new line)")
    ap.add_argument("--output", help="directory to save new/changed annotations.")
    ap.add_argument("--data", help="(optional) yolo .data file to read classes from.")
    # For auto labeling:
    #ap.add_argument("--cfg", )
    #ap.add_argument("--weights")
    args = ap.parse_args(sys.argv[1:])
    main(args)
