import json

class FileSink:
    def __init__(self, path_results, path_logs):
        self._file_results = open(path_results, 'w')
        self._file_logs = open(path_logs, 'w')

    def write(self, item):
        if item['result'] is not None:
            self._file_results.write(json.dumps(item['result'], ensure_ascii=False) + '\n')
        del item['result']
        self._file_logs.write(json.dumps(item, ensure_ascii=False) + '\n')

    def __del__(self):
        self._file_results.close()
        self._file_logs.close()

