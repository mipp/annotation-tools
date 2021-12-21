import os
import random
import zipfile
from sys import argv

import pandas as pd


def pripremi(studenti_csv, vid_dir, image_dir, max_slika=300):
    """Za svakog studenta pripremi svoju .zip datoteku za anotaciju slika.

    Korekcija anotacije  objekata na slikama izvučenih iz videa. Priprema zipove
    tako da uzima slučajni video i sve iz njega izvučene slike i pripadne
    anotacije, sve dok ne dosegne zadani broj slika.

    Args: studenti_csv: popis studenata u .csv formatu (može biti eksport s Moodle ocjene)
        vid_dir: direktorij s videima po čijim imenima gleda imena slika.
        image_dir: direktorij sa slikama i bounding box anotacijama
        max_slika: Zadani broj slika po studentu. Default=300.
    """
    max_slika = int(max_slika)
    df = pd.read_csv(studenti_csv)
    studenti = []
    for ime, prezime in zip(df.Ime, df.Prezime):
        studenti.append("{} {}".format(ime, prezime).replace(" ", "_"))

    vid_names = os.listdir(vid_dir)

    for student in studenti:
        student_videos = []
        jpgs = []
        while len(jpgs) < max_slika:
            video = random.choice(vid_names)
            student_videos.append(video)
            vid_names.remove(video)
            prefix = video[:-4] + "_"
            image_fnames = sorted(
                [
                    os.path.join(image_dir, x)
                    for x in os.listdir(image_dir)
                    if x.endswith(".jpg")
                    and x.startswith(prefix)
                    and os.path.exists(os.path.join(image_dir, x[:-3] + "txt"))
                ]
            )
            if len(image_fnames) == 0:
                # print("njet")
                continue
            jpgs.extend(image_fnames)
        print("{} {}".format(student, len(jpgs)))
        jpgs.extend([x[:-3] + "txt" for x in jpgs])
        with zipfile.ZipFile(student + ".zip", "w") as myzip:
            for f in jpgs:
                myzip.write(
                    filename=f, arcname=os.path.join("jpgs", os.path.basename(f))
                )


if __name__ == "__main__":
    if len(argv) > 3:
        pripremi(*argv[1:])
    else:
        print(
            "Usage: python pripremi_zip_za_studente.py /home/example/popis_studenata.csv /home/example/data/videos /home/example/data/videos/jpg"
        )
