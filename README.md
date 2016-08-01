# Stepic.org Video Downloader

Example of OAuth2 application for Stepic.org. 

Downloads all video files from a module (week) of a course or multiple weeks and courses.

1. Go to https://stepic.org/oauth2/applications/

2. Register your application with settings:  
`Client type: confidential`  
`Authorization Grant Type: client-credentials`

3. Add your `client_id` and `client_secret` to `settings.py`

4. Run the script

  * Download all video files from a module (week) of a course
  
    Run the script by the following command:
    
    ```
    python3 weekDownloader.py "154" "1" "." "720"
    ```
    
    Arguments:
    
    first - Course_id, second - Week index, third - folder name, forth - quality.

  * Download all video files from multiple weeks and courses
  
    Add courses which you want to download to the *courses* dictionary in the *settings.py* file.
    
    For example:
    
    ```
    courses[course_id] = [week_1, week_2, ...]
    courses["154"] = ["1", "2", "3"]
    courses[...] = [...]
    ```
    
    You could also set quality of the video by changing *quality* variable in the *settings.py* file.
    The default quality is 720.
    
    For example:
    ```
    quality = '720'
    ```
    
    Run the script by the following command:
    
    ```
    python3 multipleDownloader.py
    ```
