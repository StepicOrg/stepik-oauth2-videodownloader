import os

import weekDownloader

if __name__ == "__main__":

    # Course example.
    # course_id = "1"
    # course_weeks = ["1", "2", "3"]

    for item in course_weeks:
        argv = []
        argv.append(course_id)
        argv.append(item)

        week_id = "week_" + item

        os.mkdir(week_id)

        argv.append(week_id)

        weekDownloader.batch_main(argv)