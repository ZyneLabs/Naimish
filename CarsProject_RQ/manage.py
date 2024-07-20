import subprocess
import argparse

def run_worker():
    subprocess.run(['python', '-m', 'workers.worker'])

def run_process(args):
    module_path = f'{args.arg}.queue_task'
    subprocess.run(['python', '-m', module_path, args.command])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage RQ tasks for websites')
    parser.add_argument('command', choices=['crawl', 'parse', 'worker'], help='Command to execute')
    parser.add_argument('arg', type=str, nargs='?', default=None, help='Website name')

    args = parser.parse_args()
    print(args)
    if args.command == 'worker':
        run_worker()
    else:
        run_process(args)
