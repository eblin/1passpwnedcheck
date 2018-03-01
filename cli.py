import csv
import hashlib
import json
import re
from time import sleep

import fire
from tqdm import tqdm

from hibp import PasswordsApi


class PwnedCli:
    """
    Check 1password exported files (*.1pif) against haveibeenpwned.com/Passwords
    """

    def __init__(self, file):
        self._api = PasswordsApi()
        self._check_passwords(file)

    def _check_passwords(self, pif_file):
        """
        Check all passwords in .1pif file items against hibp password api
        and create a csv report with results.
        Each passwords is checked every 1.6 seconds for rate limiting purposes
        See: https://haveibeenpwned.com/API/v2#RateLimiting

        :param pif_file: .1pif file path
        :return: None
        """
        if not pif_file:
            return print('Please specify a file first.'
                         '\nUse --file=path/to/file.1pif')
        results = []
        pif_json = self._pif_to_json(pif_file)
        try:
            pbar = tqdm(pif_json, desc='Checking passwords')
            for item in pbar:
                # Skip if we don't have fields...
                if not item['secureContents'].get('fields'):
                    continue
                # Get username
                username = next((field['value'] for field in
                                 item['secureContents']['fields']
                                 if field.get('designation', '') == 'username'),
                                '')
                # Get plain text password
                password = next((field['value'] for field in
                                 item['secureContents']['fields']
                                 if field.get('designation', '') == 'password'),
                                None)
                # Skip if we couldn't find a password
                if not password:
                    continue
                # Update progress bar description...
                pbar.set_description('Checking %s' % item['title'])
                # Convert plain text password to SHA1
                hashed_password = hashlib.sha1(
                    password.encode('utf-8')
                ).hexdigest()
                # Check sha1 password, to see if it's been pwned
                pwned = self._api.check(hashed_password)
                # Let's parse the url and just get the hostname
                location = item.get('location', '')
                parsed_location = location[:50] + '...' \
                    if len(location) > 53 else location
                # Add to results list for reporting purposes
                results.append({
                    'Title': item['title'],
                    'Username': username,
                    'Password': password,
                    'Pwned': 'Yes' if pwned['pwned'] else 'No',
                    'Count': pwned['count'],
                    'URL': parsed_location,
                })
                # Wait 1.6 seconds before checking next item
                # APIs are limited to one per every 1500 milliseconds each
                sleep(1.6)
        except KeyError:
            raise
        finally:
            report_filename = pif_file.replace('.', '_') + '.csv'
            self._create_report(report_filename, results)

    @staticmethod
    def _pif_to_json(path):
        """
        Convert .1pif file to JSON
        :param path: .1pif file path
        :return: JSON
        """
        with open('%s/data.1pif' % path, encoding='utf-8') as pif:
            data = pif.read()

        cleaned_data = re.sub('(?m)^\*\*\*.*\*\*\*\s+', '', data)
        cleaned_data = cleaned_data.split('\n')
        cleaned_data = ','.join(cleaned_data).rstrip(',')
        cleaned_data = '[%s]' % cleaned_data

        return json.loads(cleaned_data)

    @staticmethod
    def _create_report(filename, results):
        """
        Create a csv file with results from API
        :param filename: Report filename
        :param results: Dictionary with results from API
        """
        if not results:
            return
        with open(filename, 'w') as f:
            # Create csv header from dictionary keys
            fields = results[0].keys()
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(results)

        print('All done √\nReport saved at: %s' % filename)


if __name__ == '__main__':
    fire.Fire(PwnedCli)
