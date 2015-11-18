# Stepic.org Video Downloader

Example of OAuth2 application for Stepic.org. Downloads all videofiles from a module (week) of a course.

1. Go to https://stepic.org/oauth2/applications/

2. Register your application with settings:  
`Client type: confidential`  
`Authorization Grant Type: client-credentials`

3. Paste your `client_id` and `client_secret` to `settings.py`

4. Run `python3 weekDownloader.py` with `course_id` and `week` arguments.  
For example: `python3 weekDownloader.py 91 4`
