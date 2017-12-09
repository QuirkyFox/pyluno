"""Orders Module."""
import logging

import pandas as pd

log = logging.getLogger(__name__)


class Orders(object):
    """Class with order related methods."""

    def __init__(self, main):
        """Initialise with super's main."""
        self.main = main

    def create_limit_order(self, order_type, volume, price,
                           base_account_id, counter_account_id):
        """Create a new limit order.

        :param order_type: 'buy' or 'sell'
        :param volume: the volume, in BTC
        :param price: the ZAR price per bitcoin
        :return: the order id
        """
        data = {
            'pair': self.main.pair,
            'type': 'BID' if order_type == 'buy' else 'ASK',
            'volume': str(volume),
            'price': str(price),
            'base_account_id': base_account_id,
            'counter_account_id': counter_account_id,
        }
        result = self.main.api_request('postorder', data=data,
                                       http_call='post')
        return result

    def create_market_order(self, order_type, volume,
                            base_account_id, counter_account_id):
        """Create a new market order.

        :param order_type: 'buy' or 'sell'
        :param volume: the volume of btc if sell, or currency if buy.
        :return: the order id
        """
        data = {
            'pair': self.main.pair,
            'type': 'BUY' if order_type == 'buy' else 'SELL',
            'volume': str(volume),
            'base_account_id': base_account_id,
            'counter_account_id': counter_account_id,
        }
        if order_type is 'buy':
            data['couter_volume'] = volume
        else:
            data['base_volume'] = volume
        result = self.main.api_request('marketorder', data=data,
                                       http_call='post')
        return result

    def stop_order(self, order_id):
        """Stop a specific order.

        :param order_id: The order ID
        :return: a success flag
        """
        data = {
            'order_id': order_id,
        }
        return self.main.api_request('stoporder', data=data,
                                     http_call='post')

    def stop_all_orders(self):
        """Stop all pending orders, both sell and buy.

        :return: dict of Boolean -- whether request succeeded or not for each
            order_id that was pending
        """
        pending = self.main.get_orders('PENDING')['orders']
        ids = [order['order_id'] for order in pending]
        result = {}
        for order_id in ids:
            status = self.main.stop_order(order_id)
            result[order_id] = status['success']
        return result

    def get_order(self, order_id):
        """Get an order by its ID.

        :param order_id: string	The order ID
        :return: dict order details or LunoAPIError raised
        """
        return self.main.api_request('orders/{}'.format(order_id))

    def list_trades(self, limit=None, since=None, pair=None):
        """Get list of all trades."""
        params = {
            'since': since,
            'limit': limit,
            'pair': 'XBTZAR'
        }
        #params = {'pair': self.main.pair if pair is None else pair} #seems like this was replacing the params variable and resulting in the since and limit being ignored
        trades = self.main.api_request('listtrades', params)
        return trades

    def list_trades_frame(self, limit=None, since=None, pair=None):
        """Get dataframe of all trades."""
        trades = self.list_trades(limit, since, pair)
        df = pd.DataFrame(trades['trades'])
        if not df.empty:
            df.index = pd.to_datetime(df.timestamp, unit='ms')
            df.price = df.price.apply(pd.to_numeric)
            df.volume = df.volume.apply(pd.to_numeric)
            df.base = df.base.apply(pd.to_numeric)
            df.counter = df.counter.apply(pd.to_numeric)
            df.fee_base = df.fee_base.apply(pd.to_numeric)
            df.drop('timestamp', axis=1, inplace=True)
        else:
            log.warning('Empty response from list_trades. Returning empty df')
        return df

    def get_fee_info(self, kind='auth', pair=None):
        """Get the fee info for the account."""
        params = {'pair': self.main.pair if pair is None else pair}
        return self.main.api_request('fee_info', params, kind=kind)
