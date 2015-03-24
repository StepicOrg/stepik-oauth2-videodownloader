# stepic-oauth2-videodownloader
Example of oauth2 application. Downloads all videofiles from Course by week

1) Go to https://stepic.org/oauth2/applications/

2) Register your application with settings:

<code> Client type: confidential </code>

<code> Authorization Grant Type: client-credentials </code>

3) Paste your client_id and client_secret to settings.py

4) run <code>python3 weekDownloader.py </code> with <code>course_id</code> and <code>week</code> arguments 
for example <code>python3 weekDownloader.py 91 4</code>
