import csv
import sys
from datetime import datetime
from statistics import median


def main():
    file_path = input("Enter CSV file path: ").strip()
    buckets = [[] for _ in range(24)]  # 24 buckets for each hour

    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                dt = datetime.fromisoformat(row[0])
                hour = dt.hour
                ping = float(row[1])
                mbit = float(row[2])
                buckets[hour].append((ping, mbit))
            except Exception as e:
                print(f"Skipping row due to error: {e}", file=sys.stderr)

        # Prepare data for CSV output
        hours = [f"{hour:02d}" for hour in range(24)]
        counts = []
        median_pings = []
        median_mbits = []

        for hour in range(24):
            data = buckets[hour]
            counts.append(str(len(data)))
            if data:
                pings = [x[0] for x in data]
                mbits = [x[1] for x in data]
                median_pings.append(f"{median(pings):.2f}")
                median_mbits.append(f"{median(mbits):.2f}")
            else:
                median_pings.append("N/A")
                median_mbits.append("N/A")

        writer = csv.writer(sys.stdout)
        writer.writerow(["Hour"] + hours)
        writer.writerow(["Count"] + counts)
        writer.writerow(["Median Ping"] + median_pings)
        writer.writerow(["Median Mbit"] + median_mbits)


if __name__ == "__main__":
    main()
