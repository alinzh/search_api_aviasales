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
# import networkx as nx
import copy

class ParallelWorker(multiprocessing.Process):
    def __init__(self, shared_request_queue: queue.Queue, shared_result_queue: queue.Queue, parallel_function: Callable):
        """
        shared_request_queue: Queue, obtained from `multiprocessing.Manager.Queue()`.
                              It is used to get data to process.
        shared_result_queue: Queue, obtained from `multiprocessing.Manager.Queue()`.
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
                # G, neighbor, finish, path_copy, visited, empty_list_of_paths, path_len, self.parallel_function = request_data
                G, neighbor, finish, path_copy, visited, empty_list_of_paths, path_len, _ = request_data
                result = self.parallel_function(G, neighbor, finish, path_copy, visited, empty_list_of_paths, path_len)
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
        G = request['graph']
        home = request['home']
        finish = request['finish']
        path = request['path']
        visited = request['visited']
        path_len = request['path_len']
        neighbors = request['neighbors']
        # parallel_function = request['circle_or_not']
        for neighbor in neighbors:
            # убрала or neighbors[0] == finish:
            if neighbor is None:
                continue
            edges_from_first_to_neighbor = [(G.get_edge_data(home, neighbor))[i] for i in G.get_edge_data(home, neighbor)]
            for edge_between_first_and_neighbor in edges_from_first_to_neighbor:
                visited = copy.deepcopy(visited)
                path_copy = copy.deepcopy(path)
                path_copy.append((home, neighbor, edge_between_first_and_neighbor))
                # self.shared_request_queue.put((G, neighbor, finish, path_copy, visited, [], path_len, parallel_function))
                self.shared_request_queue.put((G, neighbor, finish, path_copy, visited, [], path_len, None))
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

                # multiprocessing.util.Finalize(None, self.release(self.manager), args=(self.manager,), exitpriority=100)

            job_is_done = self.shared_request_queue.empty() and not self.shared_result_queue.empty()


            if wait_for_result and job_is_done:
                result = []
                # Aggregate response to request
                while not self.shared_result_queue.empty():
                    result.append(self.shared_result_queue.get())
                self.results_queue.put(result)
                print('результат готов')
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
        self.result_caller = result_caller

        self.requests_handler = RequestHandler(
            requests_queue=self.requests,
            results_queue=self.results,
            parallel_function=parallel_function,
            workers=workers,
        )
        self.results_handler = ResultHandler(requests_queue=self.results, caller=self.result_caller)
        # Start handlers
        self.requests_handler.start()
        self.results_handler.start()

    def request(self, data, link_on_search_request_data):
        self.result_caller = link_on_search_request_data
        self.requests.put(data)

