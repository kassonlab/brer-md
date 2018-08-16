import os


def set_working_dir(dir_info):
    """
    Checks to see if the working directory for current state of BRER simulation exists. If it does not, creates the
    directory. Then changes to that directory.
    :param dir_info: A dictionary containing data on the directory structure.
    :return:
    """
    top_dir = dir_info['top_dir']
    ensemble_num = dir_info['ensemble_num']
    iteration = dir_info['iteration']
    phase = dir_info['phase']

    working_dir = '{}/mem_{}/{}/{}'.format(top_dir, ensemble_num, iteration,
                                           phase)
    if not os.path.exists(working_dir):
        tree = [
            '{}/mem_{}'.format(top_dir, ensemble_num), '{}/mem_{}/{}'.format(
                top_dir, ensemble_num, iteration)
        ]
        for leaf in tree:
            if not os.path.exists(leaf):
                os.mkdir(leaf)
        os.mkdir(working_dir)

    os.chdir(working_dir)
