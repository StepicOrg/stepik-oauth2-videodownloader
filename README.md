# Stepic.org Video Downloader

Example of OAuth2 application for Stepic.org. 

Downloads all video files from a module (week) of a course or the whole course.

1. Go to https://stepic.org/oauth2/applications/

2. Register your application with settings:  
`Client type: confidential`  
`Authorization Grant Type: client-credentials`

3. Install requests module

```
pip install requests
```

4. Run the script

  ```
 python3 downloader.py [-h] --course_id=COURSE_ID --client_id=CLIENT_ID --client_secret=CLIENT_SECRET [--week_id=WEEK_ID] [--quality=360|720|1080] [--output_dir=.]
  ```
