import requests


class PasswordsApi(object):
    """
    Quick https://api.pwnedpasswords.com/range/ wrapper
    to check hashed passwords using k-Anonymity model
    See: https://haveibeenpwned.com/API/v2#SearchingPwnedPasswordsByRange
    """

    def __init__(self):
        self.api_uri = 'https://api.pwnedpasswords.com/range/%s'

    def check(self, hashed_password):
        """
        Call https://api.pwnedpasswords.com/range/%s

        :param hashed_password: Full SHA1 hash of password to check
        :return: Dictionary with the following keys:
        pwned (bool) True if the full hash is found False otherwise
        count (int) How many times hash has been pwned
        match (str) Matched hash
        """
        url = self.api_uri % hashed_password[:5]
        result = {'pwned': False, 'match': None, 'count': 0}
        headers = {'User-Agent': '1passpwnedcheck'}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            response = r.content.decode().lower().split('\n')
            match = [p for p in response if hashed_password[5:] in p]
            if match:
                hash_match, hash_count = match[0].strip().split(':')
                result = {
                    'pwned': True,
                    'match': hash_match,
                    'count': hash_count
                }

        return result
