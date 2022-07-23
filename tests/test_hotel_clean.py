from data_clean.hotels_clean import *
from tests.mock_data import *
from unittest import mock, TestCase


class Hotel_test(TestCase):

    @mock.patch.object(Hotels, 'raw', new_callable=mock.PropertyMock)
    def test_hotel_clean(self, mock_hotel):
        mock_hotel.return_value = Data().HOTEL_DATA
        hotels = Hotels()
        assert hotels.clean_pipe() == Ans().HOTEL_ANS

    @mock.patch.object(Booking, 'raw', new_callable=mock.PropertyMock)
    def test_booking_clean(self, mock_booking):
        mock_booking.return_value = Data().BOOKING_DATA
        hotels = Booking()
        assert hotels.clean_pipe() == Ans().BOOKING_ANS

    @mock.patch.object(Agoda, 'raw', new_callable=mock.PropertyMock)
    def test_agoda_clean(self, mock_agoda):
        mock_agoda.return_value = Data().AGODA_DATA
        hotels = Agoda()
        assert hotels.clean_pipe() == Ans().AGODA_ANS




