"""
This module is example on how to implement independent workers handling request queue.
Each worker can parallel its computation in accordance with settings.
Workers can be not equal. E.g. one worker can parallel its job into 3 processes while another one have single process.
One can implement selection of powerfull worker for heavy task and
"""

import threading
import multiprocessing
import queue
from typing import Callable, List, Iterable, Any, Union
import os

class ParallelWorker(multiprocessing.Process):
    def __init__(self, shared_request_queue: queue.Queue, shared_result_queue: queue.Queue, parallel_function: Callable):
        """
        shared_request_queue: Queue, obtained from `multiprocessing.Manager.Queue()`.
                              It is used to get data to process.
        shared_request_queue: Queue, obtained from `multiprocessing.Manager.Queue()`.
                              It is used to store processed result.
        parallel_function: Function to be computed in parallel
        """
        super().__init__(daemon=True)
        self.shared_request_queue = shared_request_queue
        self.shared_result_queue = shared_result_queue
        self.parallel_function = parallel_function
        # The process becomes available after `run` call.

    def maybe_get_request(self) -> Union[None, Any]:
        try:
            request = self.shared_request_queue.get()
        except queue.Empty:
            request = None
        return request

    def run(self):
        print(f"ParallelWorker {os.getpid()} is started")
        while True:
            request_data = self.maybe_get_request()
            if request_data is not None:
                result = self.parallel_function(request_data)
                self.shared_result_queue.put(result)

class Worker(threading.Thread):
    def __init__(self, n_processes: int, requests_queue:  multiprocessing.Queue, results_queue: multiprocessing.Queue, parallel_function: Callable):
        """
        n_processes: Number of processes to parallel computation
        results_queue: Link to queue to store results into.
        parallel_function: Function to be computed in parallel
        """
        super().__init__(name="worker", daemon=True)
        self.requests_queue = requests_queue
        self.results_queue = results_queue

        self.manager = multiprocessing.Manager()
        self.shared_request_queue = self.manager.Queue()
        self.shared_result_queue = self.manager.Queue()

        self.processes = [ParallelWorker(self.shared_request_queue, self.shared_result_queue, parallel_function) for _ in range(n_processes)]

    def maybe_get_request(self) -> Union[None, Any]:
        try:
            request = self.requests_queue.get()
        except queue.Empty:
            request = None
        return request

    def share_request(self, request: Any):
        # If one needs to be able to process iterable and non-iterable request data.
        if isinstance(request, Iterable):
            for element in request:
                self.shared_request_queue.put(element)
        else:
            self.shared_request_queue.put(request)

    def run(self):
        print("Worker is started")

        for process in self.processes:
            process.start()
        # Flag whether the worker is currently processing request.
        wait_for_result = False
        while True:
            if not wait_for_result:
                request = self.maybe_get_request()
                # Split request between processes.
                if request is not None:
                    self.share_request(request)
                    wait_for_result = True

            job_is_done = self.shared_request_queue.empty() and not self.shared_result_queue.empty()

            if wait_for_result and job_is_done:
                result = []
                # Aggregate response to request
                while not self.shared_result_queue.empty():
                    result.append(self.shared_result_queue.get())
                self.results_queue.put(result)
                wait_for_result = False

class RequestHandler:
    def __init__(self, requests_queue: queue.Queue, results_queue: queue.Queue, parallel_function: Callable, workers: List[int]):
        """
        This handler is designed to comfortably store workers.

        requests_queue: Link to queue to watch for requests.
        results_queue: Link to queue to store results into.
        parallel_function: Function to be computed in parallel
        workers: List of number proccesses per worker.
                 E.g. `workers=[3,1]` means two workers with one worker having `3` processes and one worker having `1` process.
        """
        if sum(workers) > os.cpu_count():
            message = f"This machine has {os.cpu_count()} while {sum(workers)} was given. Reduce number of workers or processes per worker"
            raise RuntimeError(message)

        self.workers = [Worker(n_processes, requests_queue, results_queue, parallel_function) for n_processes in workers]

    def start(self):
        """This method imitates `start` method of `threading.Thread` to maintain the same interface."""
        print("RequestHandler is started")

        # Launch workers
        for worker in self.workers:
            worker.start()

class ResultHandler(threading.Thread):
    def __init__(self, requests_queue: queue.Queue, caller: Callable):
        """
        requests_queue: Link to queue to watch for results.
        caller: function to be called if result is obtained.
        """
        super().__init__(name="result_handler", daemon=True)
        self.requests_queue = requests_queue
        self.caller = caller

    def run(self) -> None:
        print("ResultHandler is started")

        while True:
            result = None
            try:
                result = self.requests_queue.get()
            except queue.Empty:
                continue
            if result is not None:
                self.caller(result)

class ExampleClass:
    def __init__(self, result_caller: Callable, parallel_function: Callable, workers: List[int]=[2,2]):
        """
        result_caller: function to be called if result is obtained.
        parallel_function: Function to be computed in parallel
        workers: List of number proccesses per worker.
                 E.g. `workers=[3,1]` means two workers with one worker having `3` processes and one worker having `1` process.
        """
        self.requests = queue.Queue()
        self.results = queue.Queue()

        self.requests_handler = RequestHandler(
            requests_queue=self.requests,
            results_queue=self.results,
            parallel_function=parallel_function,
            workers=workers,
        )
        self.results_handler = ResultHandler(requests_queue=self.results, caller=result_caller)
        # Start handlers
        self.requests_handler.start()
        self.results_handler.start()

    def request(self, data):
        self.requests.put(data)


# def parallel_function(value):
#     if isinstance(value, str):
#         return value.upper()
#     elif isinstance(value, (int, float)):
#         return value ** 2

class AnotherClass:
    def __init__(self):
        self.example = ExampleClass(AnotherClass.show_response, self.parallel_function, [2, 2])

    def show_response(value):
        print(value)

    @staticmethod
    def parallel_function(value):
        if isinstance(value, str):
            return value.upper()
        elif isinstance(value, (int, float)):
            return value ** 2

    def request(self, value):
        self.example.request(value)

if __name__ == "__main__":

    # example = ExampleClass(print, parallel_function, [2, 2])
    #
    # for i in [2,3,4,5,6,7,8]:
    #     print(f"putted request: {i}")
    #     example.request(i)
    #
    # for i in "abcdef":
    #     print(f"putted request:  {i}")
    #     example.request(i)

    another = AnotherClass()
    for i in [2, 3, 4, 5, 6,7,8]:
        print(f"putted request: {i}")
        another.request(i)

    # Imitation of constant serving.
    while True:
        pass