def dfs_circle(G, airport: Any, path: Route):
    nonlocal paths
    for neighbor in graph.neighbors(airport):
        flights = []  # TODO: забрать edges между airport и neighbor из графа
        # flights = G.get_edge_data(airport, neighbor, data=True)
        for u, v, d in G.edges(data=True):
            if u == airport and v == neighbor:
                flights.append([airport, neighbor, d])
        for flight in flights:
            path_copy = copy.deepcopy(path)
            success = path_copy.append(flight)
            if success:
                if len(path_copy) == path_len - 1 and path_copy.start == neighbor:
                    # Захватываем блокировку перед добавлением маршрута в общий список
                    lock.acquire()
                    try:
                        paths.append(path_copy)
                    finally:
                        lock.release()  # Освобождаем блокировку
                elif neighbor not in visited:
                    visited[neighbor] = True
                    dfs_circle(G, neighbor, path_copy)