import requests
import json
import pandas as pd
from sqlalchemy import create_engine
import numpy
from random import random
from time import time


class PushID(object):
    """
    A class that implements firebase's fancy ID generator that creates
    20-character string identifiers with the following properties:
    1. They're based on timestamp so that they sort *after* any existing ids.
    2. They contain 72-bits of random data after the timestamp so that IDs
       won't collide with other clients' IDs.
    3. They sort *lexicographically* (so the timestamp is converted to
       characters that will sort properly).
    4. They're monotonically increasing.  Even if you generate more than one
       in the same timestamp, the latter ones will sort after the former ones.
       We do this by using the previous random bits but "incrementing" them by
       1 (only in the case of a timestamp collision).
    """

    # Modeled after base64 web-safe chars, but ordered by ASCII.
    PUSH_CHARS = ('-0123456789'
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  '_abcdefghijklmnopqrstuvwxyz')

    def __init__(self):

        # Timestamp of last push, used to prevent local collisions if you
        # pushtwice in one ms.
        self.last_push_time = 0

        # We generate 72-bits of randomness which get turned into 12
        # characters and appended to the timestamp to prevent
        # collisions with other clients.  We store the last characters
        # we generated because in the event of a collision, we'll use
        # those same characters except "incremented" by one.
        self.last_rand_chars = numpy.empty(12, dtype=int)

    def next_id(self):
        """Generates a unique_id.

        Returns:
            unique_id (string): String of length 12.
        """

        now = int(time() * 1000)
        duplicate_time = (now == self.last_push_time)
        self.last_push_time = now

        unique_id = self.get_unique_id(now)

        self.set_last_rand_char(duplicate_time)

        for i in range(12):
            unique_id += self.PUSH_CHARS[self.last_rand_chars[i]]

        return unique_id

    def get_unique_id(self, now):
        """Creates a unique id which is of length 8.

        Args:
            now (int): Current time converted to integer type.
        Returns:
            unique_id (string): String of length 8.
        """

        time_stamp_chars = numpy.empty(8, dtype=str)

        for i in range(7, -1, -1):
            time_stamp_chars[i] = self.PUSH_CHARS[now % 64]
            now = int(now / 64)

        unique_id = ''.join(time_stamp_chars)
        return unique_id

    def set_last_rand_char(self, duplicate_time):
        """Updates the last random characters.

        Args:
            duplicate_time (bool): Boolean value if time is duplicate.
        """
        if not duplicate_time:
            for i in range(12):
                # random() returns a floating point number in the
                # range(0.0, 1.0)
                self.last_rand_chars[i] = int(random() * 64)
        else:
            # If the timestamp hasn't changed since last push, use the
            # same random number, except incremented by 1.
            self.get_previous_rand_char()

    def get_previous_rand_char(self):
        """Updates the last random characters if time is duplicate."""

        for i in range(11, -1, -1):
            if self.last_rand_chars[i] == 63:
                self.last_rand_chars[i] = 0
            else:
                break
        self.last_rand_chars[i] += 1


class MigrateData(PushID):

    def __init__(self, limit, page):
        self.email_token_sql = 'SELECT email, token_id from Users'
        self.center_sql = 'select id, name from centers where deleted=false'
        self.role_sql = """select id from roles where title ILIKE %s and deleted=false; """

        self.engine = create_engine(
            "postgresql://hesbon:@localhost:5432/activo")
        url = 'https://api-prod.andela.com/api/v1/users'
        bearer_token = '{0} {1}'.format('Bearer', 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySW5mbyI6eyJpZCI6Ii1MUWRlM181NXJacXM2OExwTXExIiwiZmlyc3RfbmFtZSI6Ikhlc2JvbiIsImxhc3RfbmFtZSI6Ik1haXlvIiwiZmlyc3ROYW1lIjoiSGVzYm9uIiwibGFzdE5hbWUiOiJNYWl5byIsImVtYWlsIjoiaGVzYm9uLm1haXlvQGFuZGVsYS5jb20iLCJuYW1lIjoiSGVzYm9uIE1haXlvIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BQXVFN21BTmtERzJtYmV6amJhWDctMzNob0Y1WkNRMkFXaHExRlNPaUZTbj1zNTAiLCJyb2xlcyI6eyJGZWxsb3ciOiItS1hHeTFFQjFvaW1qUWdGaW02QyIsIkFuZGVsYW4iOiItS2lpaGZab3NlUWVxQzZiV1RhdSIsIkFwcHJlbnRpY2VzaGlwIFRUTCI6Ii1MSUx5d19BcDJuNHNNOTNsTTB5In19LCJpYXQiOjE1Njc1OTU1MDcsImV4cCI6MTU3MDE4NzUwNywiYXVkIjoiYW5kZWxhLmNvbSIsImlzcyI6ImFjY291bnRzLmFuZGVsYS5jb20ifQ.PDVsUBZjqZZfvyT5HtRUS5X6tXsPD5TCmN1JGN8VuI92t6UoW2ezdK0qS3O2cMnJlv3t08GBR7jF1IOjfdrM3PDjqkvTzTwgCLSX1C4a2--fFP98oX7Bv5wtFPcPgQmDy6139tFVnFhKoMxGhsj2r99OewevoDT8gSuOCxkOMTo')
        headers = {'Authorization': bearer_token}
        response = requests.get(url, headers=headers, params={
                                'limit': limit, 'page': page}).json()

        self.df = pd.read_json(json.dumps(response['values']))
        self.email_token_df = pd.read_sql(
            self.email_token_sql, con=self.engine)
        self.center_df = pd.read_sql(self.center_sql, con=self.engine)
        self.role_df = pd.read_sql(
            self.role_sql, con=self.engine, params=("%regular user%",))

        self.role_id = self.role_df.iloc[:1, 0].item()
        self.centers_dict = self.get_centers_from_db(self.center_df)
        self.email_list = self.email_token_df['email'].tolist()
        self.token_list = self.email_token_df['token_id'].tolist()

    def persist_data_to_db(self):
        df_ = self.process_data(self.df)
        print(len(df_))
        df_['email'] = df_['email'].apply(self.drop_existing)
        df_ = df_.drop(df_[df_['email'] == 'invalid_email'].index)
        df_ = df_.drop(df_[df_['token_id'] == 'invalid_token'].index)
        print(len(df_))
        df_.to_sql(name='users', con=self.engine,
                   if_exists='append',  index=False)

    def get_centers_from_db(self, center_df):
        centers_dict = {}
        for center in range(len(center_df)):
            center += 1
            centers_dict.update(
                {center_df.iloc[center-1:center, 1].item().lower(): center_df.iloc[center-1:center, 0].item()})
        return centers_dict

    def get_location(self, df):
        df['location'] = df['location'].apply(
            lambda x: x['name'] if x else 'None')
        df.drop(df[df['location'] == 'None'].index)
        return df

    def get_required_columns(self, df):
        df = df[['email', 'name', 'id', 'picture', 'location']]
        return df

    def set_center_id(self, df):
        df['center_id'] = df['center_id'].map({"Lagos": self.centers_dict['lagos'],
                                               "Ghana": self.centers_dict['ghana'],
                                               "Nairobi": self.centers_dict['nairobi'],
                                               "Kampala": self.centers_dict['kampala'],
                                               "New York": self.centers_dict['new york'],
                                               "Kigali": self.centers_dict['kigali'],
                                               "Cairo": self.centers_dict['cairo']})
        return df

    def set_user_id_role_id(self, df):
        df['id'] = 'id'
        df['deleted'] = False
        df['id'] = df['id'].apply(lambda x: PushID().next_id())
        df['role_id'] = self.role_id
        return df

    def drop_existing(self, x):
        if x in self.email_list or '@andela' not in x:
            return 'invalid_email'
        return x

    def check_token(self, df):
        df['token_id'] = df['token_id'].apply(
            lambda x: x if x not in self.token_list else 'invalid_token')
        return df

    def process_data(self, df):
        return(df.pipe(self.get_location)
               .pipe(self.get_required_columns)
               .rename(columns={'picture': 'image_url', 'id': 'token_id', "location": "center_id"})
               .pipe(self.set_center_id)
               .pipe(self.set_user_id_role_id)
               .pipe(self.check_token))
