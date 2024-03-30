import logging

logging.basicConfig(level=logging.DEBUG, filename="app.log",
                    format='%(asctime)s: %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging
