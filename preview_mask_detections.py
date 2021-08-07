"""
Prikazuje rezultate detekcije s detectron/maskrcnn .
Input: .csv file s rezultatima i video.
"""
import argparse
import ast
import sys
import platform
import cv2

if platform.system() == "Windows":
    import win32api # noqa

    screen_x = win32api.GetSystemMetrics(0)
    screen_y = win32api.GetSystemMetrics(1)
elif platform.system() == "Linux":
    screen_x = 2560
    screen_y = 1440
else:
    screen_x = 1024
    screen_y = 768


def ds2cv(res):
    return res[1], res[2], res[3], res[4], res[0]


def sort2cv(res):
    ul_x = res[1]
    ul_y = res[2]
    width = res[3]
    height = res[4]

    lr_x = ul_x + width
    lr_y = ul_y + height
    return ul_x, ul_y, lr_x, lr_y, res[0]


def open_mask_detections(file_name):
    dets = dict()
    frame = 0
    boxes = []
    with open(file_name) as ann_file:
        for row in ann_file:
            if row.startswith('Frame'):
                dets[frame] = boxes
                frame = int(row.strip().split(" ")[1])
                boxes = []
            else:
                boxes.append(
                    [int(ast.literal_eval(x.strip())) for x in row.strip().split(",")]
                )
    return dets


def put_annotations(img, boxes):
    box_colors = {0: (0, 200, 0), 1: (0, 0, 200), 7: (0, 0, 200)}
    font = cv2.FONT_HERSHEY_SIMPLEX
    for box in boxes:
        temp_box = box
        cv2.rectangle(
            img,
            (temp_box[0], temp_box[1]),
            (temp_box[2], temp_box[3]),
            box_colors[1],
            2,
        )
        cv2.putText(
            img,
            str(temp_box[4]),
            (temp_box[0], temp_box[1]),
            font,
            0.8,
            (0, 200, 0),
            2,
            cv2.LINE_AA,
        )
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


def detect(detections, frame_no):
    return detections[frame_no]

def tenacious_read(cap):
    current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if current_frame < total_frames - 2:
        while True:
            status, frame = cap.read()
            if status == True:
                return True, frame
    else:
        return False, []


def main(args):
    update_display = True
    vid_fname = args.video
    cap = cv2.VideoCapture(vid_fname)
    detections = open_mask_detections(args.input)
    frame_no = 1
    while cap.isOpened():
        ret, im = tenacious_read(cap)
        cv2.namedWindow("image")
        cv2.setWindowTitle("image", vid_fname)
        boxes = detect(detections, frame_no)
        while 1:
            if update_display:
                im = put_annotations(im, boxes)
                im = rescale_screen(im)
                cv2.imshow("image", im)
                update_display = False
            k = cv2.waitKey(1) & 0xFF
            if k == ord("p"):
                frame_no += 1
                update_display = True
                break
            elif k == 27:
                cv2.destroyAllWindows()
                sys.exit(0)
        update_display = True
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Preview Mask RCNN detections in video")
    ap.add_argument("input", help="Mask RCNN detections file")
    ap.add_argument("video", help="Corresponding video file.")
    args = ap.parse_args(sys.argv[1:])
    main(args)
