import sys
import os
import argparse
import mimetypes
import requests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+', help='Paths to input files (one or more)')
    parser.add_argument('-o', '--output', help='Output filename (required)', required=True)
    parser.add_argument('--url', default=os.environ.get('GOTENBERG_URL', 'http://localhost:3000'), help='Gotenberg base URL')
    parser.add_argument('--endpoint', default='/convert/html', help='Gotenberg endpoint, e.g. /convert/html or /convert/office')
    args = parser.parse_args()

    for p in args.inputs:
        if not os.path.exists(p):
            print(f'Input file not found: {p}')
            sys.exit(2)

    url = args.url.rstrip('/') + args.endpoint
    print(f'Posting to {url} ...')

    files = []
    for path in args.inputs:
        mime, _ = mimetypes.guess_type(path)
        files.append(('files', (os.path.basename(path), open(path, 'rb'), mime or 'application/octet-stream')))

    resp = requests.post(url, files=files)

    if resp.status_code != 200:
        print('Gotenberg returned', resp.status_code)
        print(resp.text[:1000])
        sys.exit(1)

    with open(args.output, 'wb') as ofh:
        ofh.write(resp.content)

    print(f'Wrote output to {args.output}')


if __name__ == '__main__':
    main()
