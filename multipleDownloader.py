"""
You could download multiple courses at once 
with help of the script from stepic.org .


Run by: 
python3 main.py

Additional notes:
1) Add courses which you want to download to the "settings.courses" dictionary.

2) You could also set quality of the video by changing "settings.quality" variable.
The default quality is 720.
"""

import os

import weekDownloader
import settings


def main():
    # Loop over courses.
    for key, value in settings.courses.items():
        course_id = key
        course_weeks = value

        # Loop over weeks in the course.
        for item in course_weeks:
            argv = [course_id, item]

            week_id = "week_" + item

            folder_name = course_id + os.sep + week_id

            argv.append(folder_name)

            argv.append(settings.quality)

            print("argv: {}".format(argv))

            try:
                # Download all videos in a particular week in the course.
                weekDownloader.main(argv)
            except (KeyError, IndexError) as E:
                print("! Error with course: ", "'" + folder_name + "',", "ErrorType: ", E)
                continue


if __name__ == "__main__":
    main()
