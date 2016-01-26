# Deployer
Sync repository from BitBucket with FTP directory, using webhooks 2.0

## Installation
1. Clone Repository
2. Create secrets.json in settings directory.
  ```json
  {
    "SECRET_KEY" : "your_secret_key",
    "GIT_USER_NAME" : "git_user_name",
    "GIT_USER_PASS" : "git_user_pass",
    "EMAIL_HOST_USER" : "your_email@domain.com",
    "EMAIL_HOST_PASSWORD" : "your_email_password"
  }
  ```

4. pip install -r requirements/base.txt
5. python manage.py makemigrations
6. python manage.py migrate
7. python manage.py createsuperuser
8. Run.

### Requirements
* Python 3.4.3
* Django==1.9.1
* GitPython==1.0.1
* gitdb==0.6.4
* psycopg2==2.6.1
* smmap==0.9.0

## Usage
1. Open 'Sites' and add/change domain name to your current domain.
2. Open FTPServers and add at FTP server details.
3. Open Listeners and add Listener, - add Production or Live server (or both). After saving, copy listener URL. 
To confirm the details press 'View on Site'  - you should see your bitBucket repository.
4. Open BitBucket Repository -> Settings -> Webhooks, press Add webhook, insert title and copy listener link, check 
  'Skip certificate verification' ans save.
5. Add mailboxes to be able to get reports.
6. Make some push to check it, you should get confirmation on email if you configured it properly.


## Contributing
1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Author

* Vitaliy Shebela (vitalik.privat@gmail.com)

## License
This file is part of Deployer.

Deployer is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Deployer is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Deployer.  If not, see <http://www.gnu.org/licenses/>.




