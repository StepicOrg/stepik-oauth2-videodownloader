import os

import weekDownloader

if __name__ == "__main__":
    # Set quality.
    quality = '720'

    courses = {}

    # Add courses.
    # Course example.
    courses["154"] = ["1", "2", "3"]

    for key, value in courses.items():
        course_id = key
        course_weeks = value

        for item in course_weeks:
            argv = [course_id, item]

            week_id = "week_" + item

            folder_name = course_id + os.sep + week_id

            try:
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
                weekDownloader.batch_main(argv)
            except (KeyError, IndexError) as E:
                print("! Error with course: ", "'" + folder_name + "',", "ErrorType: ", E)
                continue
