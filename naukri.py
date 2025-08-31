import os
import time
import random
from datetime import datetime
import requests
import sys
import re

class Naukri:
    validated = False

    def __init__(self):
        """Initialize class"""
        self.base_url = 'https://www.nma.mobi'
        self.header = {
            'Content-Type': 'application/json; charset=utf-8',
            'clientId': 'ndr01d',
            'deviceId': self.gen_random_id(),
            'AppVersion': '71',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Accept-Charset': 'UTF-8'
        }
        self.session = requests.Session()

    def gen_random_id(self):
        return ''.join(random.choice('0123456789abcdef') for _ in range(16))

    def post_login(self, userName, passWord):
        url = self.base_url + '/login/v2/login'
        json_data = {"USERNAME": userName, "ISLOGINBYEMAIL": "1", "PASSWORD": passWord}
        return self.session.post(url, json=json_data, headers=self.header)

    def get_dashboard(self):
        url = self.base_url + '/mnj/v3/dashBoard?properties=profile(isPushdownAvailable)'
        dash_response = self.session.get(url, headers=self.header)
        try:
            self.profile_id = dash_response.json().get('dashBoard').get('profileId')
        except Exception:
            print("Dashboard response error:", dash_response.text)
            self.profile_id = None

    def get_profile(self):
        url = self.base_url + '/mnj/v2/user/profiles?&expand_level=2&active=1'
        return self.session.get(url, headers=self.header)

    def update_profile(self, json_data):
        if not self.profile_id:
            print("Cannot update profile: profile_id not found")
            return
        url = self.base_url + f'/mnj/v1/user/profiles/{self.profile_id}/'
        self.session.post(url, json=json_data, headers=self.header)

    def valLogin(self, userName, passWord):
        print('Validating credentials...')
        login_response = self.post_login(userName, passWord)

        # Safely parse JSON
        try:
            resp_json = login_response.json()
        except ValueError:
            print("Login response is not JSON. Raw response:")
            print(login_response.text)
            self.validated = False
            return False

        if resp_json.get('error'):
            print('Login failed:', ', '.join(list(self.find('message', resp_json))))
            self.validated = False
            return False
        else:
            self.validated = True
            self.header['Authorization'] = 'NAUKRIAUTH id=' + resp_json.get('id', '')
            print('Login successful!')
            self.get_dashboard()
            return True

    def find(self, key, dictionary):
        for k, v in dictionary.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                yield from self.find(key, v)
            elif isinstance(v, list):
                for d in v:
                    yield from self.find(key, d)

def main():
    naukri = Naukri()

    # Read credentials from environment variables (GitHub Secrets)
    user_info = (os.getenv('NAUKRI_USER'), os.getenv('NAUKRI_PASS'))
    if not user_info[0] or not user_info[1]:
        print("Missing Naukri credentials in environment variables!")
        sys.exit(1)

    if not naukri.valLogin(*user_info):
        print("Login failed. Check credentials or response.")
        sys.exit(1)

    # Small random delay to mimic human behavior
    time.sleep(random.randint(5, 15))

    # Get current resume headline and refresh it
    try:
        pro_dic = naukri.get_profile().json()
        find_value = list(naukri.find('resumeHeadline', pro_dic))[0]
        print('Updating profile headline...')
        naukri.update_profile({'resumeHeadline': find_value})
        print('Profile updated at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        print("Error fetching/updating profile:", e)

if __name__ == '__main__':
    main()
