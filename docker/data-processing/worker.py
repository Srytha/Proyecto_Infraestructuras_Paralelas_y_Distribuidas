import gzip
from warcio.archiveiterator import ArchiveIterator
import csv
import os

def process_wet_file(wet_path, output_dir):
    output_file = os.path.join(output_dir, "news.csv")
    write_header = not os.path.exists(output_file)

    with gzip.open(wet_path, "rb") as stream, \
         open(output_file, "a", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        if write_header:
            writer.writerow(["date", "text"])

        for record in ArchiveIterator(stream):
            if record.rec_type != "conversion":
                continue

            date = record.rec_headers.get_header("WARC-Date")

            content = record.content_stream().read()
            if not content:
                continue

            text = content.decode("utf-8", errors="ignore").strip()

            if len(text) < 200:
                continue

            writer.writerow([date, text])

    print("Procesamiento WET completado")

if __name__ == "__main__":
    process_wet_file(
        "/data/raw/commoncrawl_news.warc.wet.gz",
        "/data/processed"
    )
