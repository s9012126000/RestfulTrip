from config.mongo_config import *
from config.mysql_config import *
from abc import ABC, abstractmethod
from difflib import SequenceMatcher

import pandas as pd
import time
import re


class Hotel_manager(ABC):
    @property
    @abstractmethod
    def web(self):
        pass

    @property
    def raw(self):
        col = client['personal_project'][self.web]
        query = col.find({}, {'_id': 0})
        hotels = [x for x in query]
        return hotels

    @property
    @abstractmethod
    def cleaned_hotel(self):
        pass

    @abstractmethod
    def clean_pipe(self):
        return NotImplemented

    def compare(self, cleaned, df):
        hotels = cleaned
        exist_df = df
        exist = exist_df[['name', 'id']]
        exist_dt = {
            self.normalize(x[1]['name']).lower(): x[1]['id'] for x in exist.iterrows()
        }
        update_ls = []
        insert_ls = []
        for hotel in hotels:
            name = self.normalize(hotel['name']).lower()
            if name in exist_dt:
                e_id = exist_dt[name]
                update_ls.append((hotel, e_id))
                hotels.remove(hotel)
                exist_dt.pop(name)
        for hotel in hotels:
            name = self.normalize(hotel['name']).lower()
            target_id = None
            r = 0
            for e_name in exist_dt:
                rate = SequenceMatcher(None, name, e_name).quick_ratio()
                if rate > r:
                    r = rate
                    target_id = exist_dt[e_name]
            if r > 0.8:
                exist_row = exist_df[exist_df['id'] == target_id]
                address = self.normalize(hotel['address'])
                e_address = self.normalize(exist_row['address'].values[0])
                address_rate = SequenceMatcher(None, address, e_address).quick_ratio()
                if address_rate > 0.2:
                    update_ls.append((hotel, target_id))
                    print(target_id)
                    print(name)
                    print(exist_row['name'].values[0], '\n')
                else:
                    insert_ls.append(hotel)
            elif 0.5 < r <= 0.8:
                exist_row = exist_df[exist_df['id'] == target_id]
                address = self.normalize(hotel['address'])
                e_address = self.normalize(exist_row['address'].values[0])
                address_rate = SequenceMatcher(None, address, e_address).quick_ratio()
                if address_rate > 0.6:
                    update_ls.append((hotel, target_id))
                    print(target_id)
                    print(name)
                    print(exist_row['name'].values[0], '\n')
                else:
                    insert_ls.append(hotel)
            else:
                insert_ls.append(hotel)
        print(time.perf_counter())
        return update_ls, insert_ls

    def run(self, exist_df):
        clean = self.clean_pipe()
        update, insert = self.compare(clean, exist_df)
        data = self.update(update, insert, exist_df)
        return data

    @classmethod
    def normalize(cls, text):
        replaces = {' ': '', '-': '', '(': '', ')': '', ',': '', '.': '', '．': '', '‧': ''}
        for i, j in replaces.items():
            text = text.replace(i, j).lower()
        return text

    @classmethod
    def update(cls, update_ls, insert_ls, exist_df):
        img_ls = []
        res_ls = []
        if update_ls:
            for up in update_ls:
                hotel = up[0]
                exist_row = exist_df[exist_df['id'] == up[1]]
                if exist_row['address'].values[0] == 'non-provided':
                    exist_df.loc[exist_df.id == up[1], 'address'] = hotel['address']
                if len(hotel['des']) > len(exist_row['des']):
                    exist_df.loc[exist_df.id == up[1], 'des'] = hotel['des']
                if hotel['star'] != 0 and exist_row['star'].values[0] == 0.0:
                    exist_df.loc[exist_df.id == up[1], 'star'] = float(hotel['star'])
                img_pack = {
                    'hotel_id': up[1],
                    'resource': hotel['resource'],
                    'image': hotel['img']
                }
                resource_pack = {
                    'resource': hotel['resource'],
                    'url': hotel['url'],
                    'rating': hotel['rating'],
                    'hotel_id': up[1]
                }
                img_ls.append(img_pack)
                res_ls.append(resource_pack)

        hotel_id = exist_df.sort_values(['id'])['id'].iloc[-1]

        if insert_ls:
            hotels = []
            for new_hotel in insert_ls:
                hotel_id += 1
                hotel_pack = {
                    'id': hotel_id,
                    'name': new_hotel['name'],
                    'address': new_hotel['address'],
                    'des': new_hotel['des'],
                    'star': new_hotel['star']
                }
                img_pack = {
                    'hotel_id': hotel_id,
                    'resource': new_hotel['resource'],
                    'image': new_hotel['img'],
                }
                resource_pack = {
                    'resource': new_hotel['resource'],
                    'url': new_hotel['url'],
                    'rating': new_hotel['rating'],
                    'hotel_id': hotel_id
                }
                hotels.append(hotel_pack)
                img_ls.append(img_pack)
                res_ls.append(resource_pack)
            insert_df = pd.DataFrame(hotels)
            new_df = pd.concat([exist_df, insert_df])
        else:
            new_df = exist_df
        return new_df, img_ls, res_ls

    @classmethod
    def get_current_sql(cls):
        MyDb.ping(reconnect=True)
        cursor = MyDb.cursor()
        cursor.execute('SELECT * FROM hotels')
        hotels_ls = cursor.fetchall()
        MyDb.commit()
        df = pd.DataFrame(hotels_ls)
        return df

    def first_insert(self):
        MyDb.ping(reconnect=True)
        cursor = MyDb.cursor()
        cursor.execute("SELECT id FROM hotels ORDER BY id DESC LIMIT 1")
        last_id = cursor.fetchone()
        MyDb.commit()
        if not last_id:
            hotel_id = 0
        else:
            hotel_id = last_id['id']
        hotel_vals = []
        res_vals = []
        img_vals = []
        for hotel in self.cleaned_hotel:
            hotel_id += 1
            hotel_val = (hotel_id, hotel['name'], hotel['address'], hotel['des'], hotel['star'])
            res_val = (hotel['resource'], hotel['url'], hotel['rating'], hotel_id)
            img_val = (hotel['img'], hotel['resource'], hotel_id)
            hotel_vals.append(hotel_val)
            res_vals.append(res_val)
            img_vals.append(img_val)
        h_place = ', '.join(['%s'] * len(hotel_vals[0]))
        r_place = ', '.join(['%s'] * len(res_vals[0]))
        i_place = ', '.join(['%s'] * len(img_vals[0]))
        hotel_sql = f"INSERT INTO hotels (id, name, address, des, star) VALUES ({h_place})"
        res_sql = f"INSERT INTO resources (resource, url, rating, hotel_id) VALUES ({r_place})"
        img_sql = f"INSERT INTO images (image, resource, hotel_id) VALUES ({i_place})"
        cursor.executemany(hotel_sql, hotel_vals)
        cursor.executemany(res_sql, res_vals)
        cursor.executemany(img_sql, img_vals)
        MyDb.commit()

    def __repr__(self):
        return str(f"{len(self.raw)} raw hotels")

    def __len__(self):
        return len(self.raw)


class Hotels(Hotel_manager, ABC):
    @property
    def web(self):
        return 'hotels'

    @property
    def cleaned_hotel(self):
        data = self.clean_pipe()
        return data

    def clean_pipe(self):
        check_ls = []
        hotels = self.raw.copy()
        for d in self.raw:
            if d['detail'] in check_ls:
                hotels.remove(d)
            else:
                check_ls.append(d['detail'])
        hotel_ls = []
        name_ls = []
        for d in hotels:
            name = d['detail'].split('\n')[0]
            if name in ['VIP Access', '整棟度假屋', '整間出租公寓', '整間木屋']:
                part = 1
            else:
                part = 0
            name = d['detail'].split('\n')[part]
            address = d['address']
            if name in name_ls:
                name = name + '-' + address.split(' ')[0]
            name_ls.append(name)
            des = d['detail'].split('\n')[-1]
            try:
                star = float(re.search(r"\d\.\d", d['detail']).group())
            except AttributeError:
                star = 0.0
            img = d['img']
            url = d['url']
            rating = '，來自 '.join(d['rating'].split('\n')[0:2])
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 1,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)
        return hotel_ls


class Booking(Hotel_manager, ABC):
    @property
    def web(self):
        return 'booking'

    @property
    def cleaned_hotel(self):
        data = self.clean_pipe()
        return data

    def clean_pipe(self):
        check_ls = []
        hotels = self.raw.copy()
        for d in self.raw:
            if d['name'] in check_ls:
                hotels.remove(d)
            else:
                check_ls.append(d['name'])
        hotel_ls = []
        for d in hotels:
            name = d['name'].split('\n')[-2]
            address = d['address'].replace('\n', '').strip()
            des = d['des'].strip().replace('\n', '')
            star = d['star']
            img = d['img']
            url = d['url']
            rating = d['rating']
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 2,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)
        return hotel_ls


class Agoda(Hotel_manager, ABC):
    @property
    def web(self):
        return 'agoda'

    @property
    def cleaned_hotel(self):
        data = self.clean_pipe()
        return data

    def clean_pipe(self):
        check_ls = []
        hotels = self.raw.copy()
        for d in self.raw:
            if d['name'] in check_ls:
                hotels.remove(d)
            else:
                check_ls.append(d['name'])
        hotel_ls = []
        for d in hotels:
            name = d['name']
            name = name.split('(')[0].split('（')[0]
            address = self.normalize(d['address'])
            try:
                pat = re.search(r"[a-z\d’~']+", address)
                start = pat.end()
                sli = pat.group()
                if len(sli) > 3:
                    address = address[start:]
            except AttributeError:
                pass
            des = d['des']
            star = d['star']
            if 'pink' in star:
                star = 0.0
            elif 'orange' in star:
                try:
                    star = float('.'.join(re.search(r"star-(\d+)", star).group(1)))
                except AttributeError:
                    star = 0.0
            img = d['img']
            url = d['url']
            rating = d['rating'].replace('\n', '，')
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 3,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)
        return hotel_ls


if __name__ == '__main__':
    hotels = Hotels()
    booking = Booking()
    agoda = Agoda()
    pipline = [hotels, booking, agoda]

    image_ls, resource_ls = [], []
    current_hotel = hotels.get_current_sql()
    for job in pipline:
        try:
            data_pack = job.run(current_hotel)
            current_hotel = data_pack[0]
            image_ls.extend(data_pack[1])
            resource_ls.extend(data_pack[2])
        except KeyError:
            job.first_insert()
            current_hotel = hotels.get_current_sql()
            data_pack = job.run(current_hotel)
            current_hotel = data_pack[0]

    hotels_to_sql(current_hotel)
    dt_to_sql('images', image_ls)
    dt_to_sql('resources', resource_ls)
