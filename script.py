import json


def main():
    data = []

    with open("results.jsonl", encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    print(data[0])


if __name__ == '__main__':
    main()
