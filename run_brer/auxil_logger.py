import logging


class Auxiliary:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('BRER')
        self.logger.info(' Creating instance of BRER logger')

    def log_phase_complete(self, phase):
        self.logger.info(' completed phase {}'.format(phase))

    def initialized(self, foo):
        self.logger.info(' initialized {}'.format(foo))

    def read_from_file(self, foo):
        self.logger.info(' read {} into memory'.format(foo))

    def report_parameter(self, key, value):
        self.logger.info(' {} = {}'.format(key, value))


if __name__ == "__main__":

    aux = Auxiliary()
    aux.log_phase_complete('training')
