
"""
Expose catsHTM.cone_search over a zerorpc interface. This allows you to query
the catalog from a machine that does not have the files locally.
"""

import os
import logging
import zerorpc
import backoff

try:
    from catsHTM import cone_search
    class catsHTMFacade:
        def __init__(self, *args, **kwargs):
            self.catalogs = kwargs.pop('catalogs')
            super(catsHTMFacade, self).__init__(*args, **kwargs)
        def cone_search(self, *args, **kwargs):
            kwargs['catalogs_dir'] = self.catalogs
            srcs, colnames, colunits = cone_search(*args, **kwargs)
            # msgpack can only serialize JSON types, so we convert arrays to lists
            return srcs.tolist(), colnames.tolist(), colunits.tolist() 

    class catsHTMServer(catsHTMFacade, zerorpc.Server):
        pass
except ImportError as server_err:
    pass

log = logging.getLogger('catshtm_client')

def on_backoff(details):
    details['method'] = details['args'][1]
    details['args'] = details['args'][2:]
    log.info("Backing off {wait:0.1f}s after {tries} tries "
           "calling {method}{args}".format(**details))

try:
    import zerorpc
    import backoff

    class catsHTMClient(zerorpc.Client):
        @backoff.on_exception(backoff.expo,
            zerorpc.exceptions.LostRemote,
            logger=None, on_backoff=on_backoff)
        def __call__(self, method, *args, **kwargs):
            return super().__call__('cone_search', *args, **kwargs)
except ImportError as client_err:
    pass

_CLIENTS = {}

def get_client(address):
    """
    Get a catsHTM client for the given address.
    :param address: either a ZeroMQ addres of the form tcp://HOST:PORT or a local filesystem path
    """
    if address in _CLIENTS:
        pass
    elif address.startswith('tcp://'):
        try:
            _CLIENTS[address] = catsHTMClient(address)
        except NameError:
            raise server_err
    elif os.path.isdir(address):
        try:
            _CLIENTS[address] = catsHTMFacade(catalogs=address)
        except NameError:
            raise client_err
    else:
        raise ValueError("{} is neither a ZeroMQ address nor a directory")
    return _CLIENTS[address]

def run():
    
    def readable_dir(prospective_dir):
        if not os.path.isdir(prospective_dir):
            raise TypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise TypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))
    
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('catalog_dir', type=readable_dir, help="directory containing catsHTM files")
    parser.add_argument('--port', type=int, default=27025, help='port to listen on')
    opts = parser.parse_args()

    logging.basicConfig(level='WARN', format="(%(asctime)s %(levelname)s) %(message)s",datefmt='%H:%M')

    server = catsHTMServer(catalogs=opts.catalog_dir)
    server.bind('tcp://*:{}'.format(opts.port))
    try:
        server.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run()
