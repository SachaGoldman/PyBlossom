from collections import deque


class Graph:
    """A graph in which the maximum matching can be obtained using the blossom algorithm"""

    _verticies: list['_Vertex']
    _free_verticies: list['_Vertex']
    _root: '_Vertex'

    class _Vertex:
        """A vertex in the graph"""

        children: list['_Vertex']
        neighbors: list['_Vertex']
        parent: '_Vertex'
        mate: '_Vertex'
        super_vertex: '_Vertex'

        def __init__(self):
            self.children = []
            self.neighbors = []
            self.parent = None
            self.mate = None
            self.super_vertex = None

        def contains(self, vertex: '_Vertex') -> bool:
            """Check if <vertex> is a part of this vertex"""

            return self is vertex

        def get_super(self) -> '_Vertex':
            """Get the most super vertex that this vertex is a part of"""

            if self.super_vertex is None:
                return self
            else:
                return self.super_vertex.get_super()

        def get_neighbors(self) -> list['_Vertex']:
            """Get a lsit of neighbors that this vertex has"""

            return self.neighbors

        def clear_tree_info(self):
            """Clear any info about this vertexs placment in the tree"""

            self.children = []
            self.parent = None
            self.super_vertex = None

        def make_child(self, child: '_Vertex'):
            """makes <child> a child of this vertex"""
            child.parent = self
            self.children.append(child)

    class _SuperVertex(_Vertex):
        """A super vertex containing the vertices in <blossom>"""

        blossom: list['_Vertex']

        def __init__(self, blossom):
            super().__init__()
            self.blossom = blossom
            self.mate = blossom[0].mate
            self.parent = blossom[0].parent
            for vertex in self.blossom:
                vertex.super_vertex = self

        def get_neighbors(self) -> list['_Vertex']:
            neighbors = []

            for pedal in self.blossom:
                for neighbor in pedal.get_neighbors():
                    if not self.contains(neighbor):
                        neighbors.append(neighbor)

            return neighbors

        def contains(self, vertex: '_Vertex') -> bool:
            for pedal in self.blossom:
                if pedal is vertex or pedal.contains(vertex):
                    return True

            return False

        def get_through_path(self, entered_by_mate: bool, before_vertex: '_Vertex',
                             after_vertex: '_Vertex') -> list['_Vertex']:
            """Get a path from <before_vertex> to <after_vertex> through this super vertex"""

            exit_found = False
            entrence_found = False

            # Check to see if we are trying to get the parent
            if after_vertex is None:
                exit_found = True
                after_vertex = self.parent
                blossom_exit_index = 0

            # Find the entrence and exit
            for i in range(len(self.blossom)):
                pedal = self.blossom[i]

                if not entrence_found:
                    if entered_by_mate:
                        if pedal.contains(before_vertex.mate):
                            blossom_entrence_index = i
                            entrence_found = True
                    else:
                        if before_vertex in pedal.get_neighbors():
                            blossom_entrence_index = i
                            entrence_found = True

                if not exit_found:
                    if not entered_by_mate:
                        if pedal.contains(after_vertex.mate):
                            blossom_exit_index = i
                            exit_found = True
                    else:
                        for neighbor in pedal.get_neighbors():
                            if after_vertex.contains(neighbor):
                                blossom_exit_index = i
                                exit_found = True

            # Create the two paths
            if blossom_exit_index < blossom_entrence_index:
                path1 = self.blossom[blossom_entrence_index:blossom_exit_index:-1] + [
                    self.blossom[blossom_exit_index]]
                path2 = self.blossom[blossom_entrence_index:] + \
                    self.blossom[:blossom_exit_index + 1]
            else:
                path1 = self.blossom[blossom_entrence_index:blossom_exit_index + 1]
                path2 = self.blossom[blossom_entrence_index::-1] + \
                    self.blossom[-1:blossom_exit_index:-1] + \
                    [self.blossom[blossom_exit_index]]

            if len(path1) % 2 == 0:
                even_path, odd_path = path1, path2
            else:
                odd_path, even_path = path1, path2

            # Pick the right path
            if after_vertex is None and entered_by_mate:
                path = even_path
            else:
                path = odd_path

            # Call this method recursively to make sure each element of
            # the final path is not a super vertex
            last_vertex = before_vertex
            exit_path = []

            for i in range(len(path)):
                pedal = path[i]

                if isinstance(pedal, Graph._SuperVertex):
                    if i + 1 < len(path):
                        next_vertex = path[i + 1]
                    else:
                        next_vertex = after_vertex

                    last_by_mate = pedal.mate is last_vertex

                    exit_path.extend(pedal.get_through_path(
                        last_by_mate, last_vertex, next_vertex))
                else:
                    exit_path.append(pedal)

                last_vertex = exit_path[-1]

            return exit_path

    def __init__(self, size: int):
        self._verticies = [self._Vertex() for _ in range(size)]
        self._free_verticies = None
        self._root = None

    def find_max_matched(self) -> int:
        """Find how many verticies there are in the maximum matching"""

        for vertex in self._verticies:
            vertex.mate = None

        # Create the list of unmatched verticies
        self._free_verticies = self._verticies[:]

        # While there are unmatched and uncheck verticies keep checking
        while self._free_verticies:
            self._find_path()

        return len([vertex for vertex in self._verticies if vertex.mate is not None])

    def _find_path(self):
        """Find a path between to free verticies"""

        queue = deque()

        for vertex in self._verticies:
            vertex.clear_tree_info()

        # Start with a free vertex
        self._root = self._free_verticies.pop()
        queue.append(self._root)

        # Begin modifed BFS
        while queue:
            vertex = queue.popleft()

            for neighbor in vertex.get_neighbors():
                if vertex.get_super() is vertex:
                    neighbor = neighbor.get_super()

                    if not self._in_tree(neighbor) and neighbor.mate is not None:
                        # Add this neighbor and its mate to the BFS tree
                        vertex.make_child(neighbor)
                        neighbor.make_child(neighbor.mate)
                        queue.append(neighbor.mate)
                    elif self._in_tree(neighbor):
                        # Check the cardinality of the cycle and if nessacary make a blossom
                        cycle = self._find_cycle(neighbor, vertex)

                        if len(cycle) % 2 == 1:
                            queue.append(self._SuperVertex(cycle))
                    elif neighbor.mate is None and not isinstance(neighbor, Graph._SuperVertex):
                        # Expand the path and use it to augment the matching
                        vertex.make_child(neighbor)
                        augmenting_path = self._expand_augmenting_path(
                            neighbor)

                        self._augment_match(augmenting_path)
                        return

    def _expand_augmenting_path(self, start: _Vertex) -> list[_Vertex]:
        """Make the path defined by the parent pointers of <start> into one without super verticies"""

        path = [start]

        while path[-1].parent is not None:
            current_vertex = path[-1].parent.get_super()

            # If this path is a super vertex then find a path through it using regular verticies
            if isinstance(current_vertex, self._SuperVertex):
                last_vertex = path[-1]
                next_vertex = current_vertex.parent

                entered_by_mate = current_vertex.mate is last_vertex

                path.extend(current_vertex.get_through_path(
                    entered_by_mate, last_vertex, next_vertex))
            else:
                path.append(current_vertex)

        return path

    def _augment_match(self, path: list[_Vertex]):
        """Augment the current matching using the <path>"""
        self._free_verticies.remove(path[0])

        for i in range(0, len(path), 2):
            path[i].mate, path[i + 1].mate = path[i + 1], path[i]

    def add_edge(self, i: int, j: int):
        """Add an edge between the ith and jth verticies"""

        self._verticies[i].neighbors.append(self._verticies[j])
        self._verticies[j].neighbors.append(self._verticies[i])

    def _find_cycle(self, vertex1: _Vertex, vertex2: _Vertex) -> list[_Vertex]:
        """Find the cycle including <vertex1> and <vertex2>"""

        root_to_vertex1 = [vertex1]
        while root_to_vertex1[-1].parent is not None:
            root_to_vertex1.append(root_to_vertex1[-1].parent.get_super())
        root_to_vertex1.reverse()

        root_to_vertex2 = [vertex2]
        while root_to_vertex2[-1].parent is not None:
            root_to_vertex2.append(root_to_vertex2[-1].parent.get_super())
        root_to_vertex2.reverse()

        # Find the common ancestor of our verticies
        common_ancestor_index = 0

        while len(root_to_vertex1) > common_ancestor_index + 1 and \
                len(root_to_vertex2) > common_ancestor_index + 1 and \
                root_to_vertex1[common_ancestor_index + 1] is \
                root_to_vertex2[common_ancestor_index + 1]:
            common_ancestor_index += 1

        # Connect the paths to the ancestor
        cycle_part1 = root_to_vertex1[common_ancestor_index:]
        cycle_part2 = root_to_vertex2[-1:common_ancestor_index:-1]

        return cycle_part1 + cycle_part2

    def _in_tree(self, vertex: _Vertex) -> bool:
        """Check if <vertex> is in the BFS tree"""
        return vertex.parent is not None or vertex is self._root
