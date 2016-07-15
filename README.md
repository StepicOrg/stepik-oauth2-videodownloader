# Stepic.org Video Downloader

Example of OAuth2 application for Stepic.org. Downloads all videofiles from a module (week) of a course.

1. Go to https://stepic.org/oauth2/applications/

2. Register your application with settings:  
`Client type: confidential`  
`Authorization Grant Type: client-credentials`

3. Add your `client_id` and `client_secret` to the system environment variable.

4. Add courses which you want to download to the *courses* dictionary in the *main.py* file.

  For example:
  ```
  courses[course_id] = [week_1, week_2, ...]
  courses["154"] = ["1", "2", "3"]
  courses[...] = [...]
  ```

  You could also set quality of the video by changing *quality* variable in the *main.py* file.
  The default quality is 720.
  
  For example:
  ```
  quality = '720'
  ```

5. Run `python3 main.py`
