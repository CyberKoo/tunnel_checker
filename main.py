#!/usr/bin/env python3
import argparse
import logging
import os
import shutil
import subprocess
import sys

import icmplib
from datetime import datetime

import requests
from netaddr import IPSet

import db


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def get_loss_rate_history(lines=5):
    res = db.query('select avg(loss) from (select loss from probe_history order by id desc limit ?)', (lines,))
    return res.fetchone()[0]


def update_loss_rate():
    data = _get_package_loss()
    db.query('insert into probe_history(min_rtt, max_rtt, sent, received, loss, timestamp) values(?, ?, ?, ?, ?, ?)',
             (data['min_rtt'], data['max_rtt'], data['sent'], data['received'], data['loss'], datetime.now()))


def _get_package_loss(host='1.2.4.8'):
    result = icmplib.ping(host, 10, 0.5, 1)

    return {'min_rtt': result.min_rtt, 'max_rtt': result.max_rtt, 'sent': result.packets_sent,
            'received': result.packets_received, 'loss': result.packet_loss}


def count_route_table(nic):
    executable = shutil.which('ip')
    command = '{} route | grep {} | wc -l'.format(executable, nic)
    return int(subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8'))


def get_china_ip4():
    url = 'https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt'
    rules = requests.get(url).content
    return IPSet(rules.decode('utf-8').strip().split('\n'))


def add_route(ip, interface):
    executable = shutil.which('ip')
    command = '{} route add {} dev {}'.format(executable, ip, interface)
    subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')


def manipulate_route_table(action, interface):
    executable = shutil.which('ip')
    command_template = '{} route {} {} dev {}'

    for ip in get_china_ip4().iter_cidrs():
        command = command_template.format(executable, action, ip, interface)
        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        except subprocess.CalledProcessError as e:
            logging.error('执行命令 {} 时发生错误', command)


def get_arg_parser():
    parser = argparse.ArgumentParser(description='GRE Tunnel Checker')
    parser.add_argument('--interface', required=True, help='GRE Tunnel Interface')

    return parser.parse_args()


def main():
    args = get_arg_parser()
    db.init('{}/db.sqlite3'.format(get_script_path()))

    update_loss_rate()
    db.commit()

    if count_route_table(args.interface) < 200:
        if get_loss_rate_history() < 0.15:
            manipulate_route_table('add', args.interface)
            logging.info('网络状态良好，增加GRE隧道路由表')
    else:
        if get_loss_rate_history() >= 0.15:
            manipulate_route_table('del', args.interface)
            logging.info('网络状态不佳，移除GRE隧道路由表')

    db.close()


if __name__ == '__main__':
    # set logger
    logging.basicConfig(
        format='%(asctime)s [%(processName)s] [%(threadName)s] [%(levelname)8s]  %(message)s',
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )

    main()
