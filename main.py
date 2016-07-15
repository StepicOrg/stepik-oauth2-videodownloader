"""
You could download multiple courses at once 
with help of the script from stepic.org .


Run by: 
python3 main.py

Additional notes:
1) Add courses which you want to download to the "courses" dictionary.

2) You could also set quality of the video by changing "quality" variable. 
The default quality is 720.
"""

import os

import weekDownloader

def main():
    # Set the quality of a video.
    quality = '720'

    courses = {}

    # Add courses.
    # courses[course_id] = [week_1, week_2, ...]

    # Course example.
    courses["154"] = ["1", "2", "3"]

    # Loop over courses.
    for key, value in courses.items():
        course_id = key
        course_weeks = value

        # Loop over weeks in the course.
        for item in course_weeks:
            argv = [course_id, item]

            week_id = "week_" + item

            folder_name = course_id + os.sep + week_id

            try:
                # Create a directory for a particular week in the course.
                os.makedirs(folder_name)
            except PermissionError:
                print("Run the script from admin")
                exit(1)
            except FileExistsError:
                print("Please delete the folder " + folder_name)
                exit(1)

            argv.append(folder_name)

            argv.append(quality)

            print("argv: {}".format(argv))

            try:
                # Download all videos in a particular week in the course.
                weekDownloader.batch_main(argv)
            except (KeyError, IndexError) as E:
                print("! Error with course: ", "'" + folder_name + "',", "ErrorType: ", E)
                continue


if __name__ == "__main__":
    main()