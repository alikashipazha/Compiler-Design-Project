from typing import Dict, List, Optional, Set, Tuple
from cc_analyzer.analysis.cfg import CFG, BasicBlock

class DominanceAnalyzer:
    """Computes the Dominator Tree using the Lengauer-Tarjan algorithm 
    and computes the Dominance Frontier for a given CFG (Section 7 - Bonus)."""
    
    def __init__(self, cfg: CFG):
        self.cfg = cfg
        # Immediate Dominator mapping: Block -> Block
        self.idom: Dict[BasicBlock, BasicBlock] = {}
        # Dominance Frontier mapping: Block -> Set[Blocks]
        self.df: Dict[BasicBlock, Set[BasicBlock]] = {b: set() for b in cfg.blocks}

    def analyze(self):
        """Executes Lengauer-Tarjan and computes the dominance frontiers."""
        reachable_blocks = self.cfg.get_reachable_blocks()
        if not reachable_blocks:
            return

        # Filter out unreachable blocks to ensure mathematical consistency
        blocks_to_process = [b for b in self.cfg.blocks if b in reachable_blocks]
        n_blocks = len(blocks_to_process)

        # Disjoint-Set Forest structures for evaluation and path compression
        ancestor: Dict[BasicBlock, Optional[BasicBlock]] = {b: None for b in blocks_to_process}
        label: Dict[BasicBlock, BasicBlock] = {b: b for b in blocks_to_process}
        
        # Lengauer-Tarjan numbering and parents
        dfnum: Dict[BasicBlock, int] = {}
        vertex: List[Optional[BasicBlock]] = [None] * (n_blocks + 1)
        parent: Dict[BasicBlock, Optional[BasicBlock]] = {b: None for b in blocks_to_process}
        semi: Dict[BasicBlock, int] = {}
        bucket: Dict[BasicBlock, Set[BasicBlock]] = {b: set() for b in blocks_to_process}

        # Step 1: Perform DFS and number nodes (1-based index)
        dfs_counter = 0
        visited: Set[BasicBlock] = set()

        def dfs(curr: BasicBlock):
            nonlocal dfs_counter
            visited.add(curr)
            dfs_counter += 1
            dfnum[curr] = dfs_counter
            vertex[dfs_counter] = curr
            semi[curr] = dfs_counter

            for succ in curr.successors:
                if succ in reachable_blocks and succ not in visited:
                    parent[succ] = curr
                    dfs(succ)

        dfs(self.cfg.entry)

        # Disjoint-Set forest helpers
        def compress(v: BasicBlock):
            anc = ancestor[v]
            if anc is not None and ancestor[anc] is not None:
                compress(anc)
                if semi[label[anc]] < semi[label[v]]:
                    label[v] = label[anc]
                ancestor[v] = ancestor[anc]

        def evaluate(v: BasicBlock) -> BasicBlock:
            if ancestor[v] is None:
                return v
            compress(v)
            return label[v]

        def link(v: BasicBlock, w: BasicBlock):
            ancestor[w] = v

        # Step 2 & 3: Compute semi-dominators and partial immediate dominators
        # Iterate in reverse DFS order (excluding entry node at dfnum 1)
        for i in range(dfs_counter, 1, -1):
            w = vertex[i]
            if w is None:
                continue

            # Compute semi[w] by inspecting predecessors
            for pred in w.predecessors:
                if pred not in dfnum:
                    continue  # Skip unreachable predecessors
                u = evaluate(pred)
                if semi[u] < semi[w]:
                    semi[w] = semi[u]

            # Add w to the bucket of its semi-dominator
            semi_v = vertex[semi[w]]
            if semi_v:
                bucket[semi_v].add(w)

            # Link w to its DFS parent
            p = parent[w]
            if p:
                link(p, w)

            # Evaluate nodes in parent's bucket
            if p:
                for v in list(bucket[p]):
                    u = evaluate(v)
                    # If semi[u] < semi[v], idom is u; else, it is parent
                    self.idom[v] = u if semi[u] < semi[v] else p
                bucket[p].clear()

        # Step 4: Adjust and refine immediate dominators in forward DFS order
        for i in range(2, dfs_counter + 1):
            w = vertex[i]
            if w is None:
                continue
            p = parent[w]
            semi_w_v = vertex[semi[w]]
            if self.idom[w] != semi_w_v:
                self.idom[w] = self.idom[self.idom[w]]

        # ENTRY block is dominated by itself
        self.idom[self.cfg.entry] = self.cfg.entry

        # Step 5: Compute Dominance Frontiers (Section 7 rules)
        # For each node b in the CFG, if it is a join point (predecessors > 1)
        for b in blocks_to_process:
            if len(b.predecessors) > 1:
                for pred in b.predecessors:
                    runner = pred
                    while runner != self.idom[b] and runner != self.cfg.entry:
                        if runner in self.df:
                            self.df[runner].add(b)
                        runner = self.idom[runner]

    def get_idom(self, block: BasicBlock) -> Optional[BasicBlock]:
        return self.idom.get(block)

    def get_dominance_frontier(self, block: BasicBlock) -> Set[BasicBlock]:
        return self.df.get(block, set())

    def get_dominator_tree_structure(self) -> Dict[BasicBlock, List[BasicBlock]]:
        """Constructs an adjacency list representing the Dominator Tree structure."""
        tree: Dict[BasicBlock, List[BasicBlock]] = {b: [] for b in self.cfg.blocks}
        for child, parent in self.idom.items():
            if child != parent and parent in tree:
                tree[parent].append(child)
        return tree