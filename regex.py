from typing import List, Dict, Set, Hashable
from collections import defaultdict

NFAState = Hashable

EPSILON = ""

class NFA:
    def __init__(self, states: List[NFAState], start: NFAState):
        self.states = states
        self.start = start
        self.accept = set()
        self.trasitions: Dict[NFAState, Dict[str, Set[NFAState]]] = defaultdict(
            lambda: defaultdict(set)
        )

    def add_transition(self, src: NFAState, dest: NFAState, symbol: str):
        self.trasitions[src][symbol].add(dest)

    def add_state(self, state: NFAState):
        self.states.append(state)

    def add_accept(self, state: NFAState):
        assert state in self.states, "State must be added before it can be accepted"
        self.accept.add(state)

    def match(self, string: str) -> bool:
        current_states = {self.start}
        for symbol in string:
            next_states = set()
            for state in current_states:
                next_states |= self.trasitions[state][symbol]
                next_states |= self.trasitions[state][EPSILON]
            current_states = next_states
        return bool(
            current_states & self.accept
        )  # check if any accept state is in current states

    def copy(self) -> "NFA":
        # create a deep copy of the NFA (but states are maintained)
        new_nfa = NFA(self.states, self.start)
        new_nfa.accept = self.accept.copy()
        new_nfa.trasitions = defaultdict(lambda: defaultdict(set))
        for state, transitions in self.trasitions.items():
            for symbol, dest_states in transitions.items():
                new_nfa.trasitions[state][symbol] = dest_states.copy()
        return new_nfa
    
    def union(self, other: "NFA") -> "NFA":
        # the resulting NFA will accept strings that either self or other do
        new_nfa = self.copy()
        new_nfa.states += other.states
        new_nfa.accept |= other.accept
        old_starts = new_nfa.start, other.start
        start = State()
        new_nfa.start = start
        new_nfa.add_transition(start, old_starts[0], EPSILON)
        new_nfa.add_transition(start, old_starts[1], EPSILON)
        return new_nfa

    def concat(self, other: "NFA") -> "NFA":
        # the resulting NFA will accept string that are accepted by self followed by other
        new_nfa = self.copy()
        new_nfa.states += other.states
        for accept in new_nfa.accept:
            new_nfa.add_transition(accept, other.start, EPSILON)
        new_nfa.accept = other.accept
        return new_nfa

    def star(self) -> "NFA":
        start_and_accept = State()
        new_nfa = self.copy()
        old_start = new_nfa.start
        new_nfa.start = start_and_accept
        
        new_nfa.add_transition(new_nfa.start, old_start, EPSILON)
        for accept in new_nfa.accept:
            new_nfa.add_transition(accept, new_nfa.start, EPSILON)
        new_nfa.accept = {start_and_accept}

        return new_nfa
    
    def vizualize(self):
        import matplotlib.pyplot as plt
        import networkx as nx

        G = nx.DiGraph()

        for state in self.states:
            if state == self.start:
                G.add_node(state, shape="circle", color="green", style="filled")
            elif state in self.accept:
                G.add_node(state, shape="circle", color="red", style="filled")
            else:
                G.add_node(state, shape="circle", color="blue", style="filled")

        for src, transitions in self.trasitions.items():
            for symbol, dest_states in transitions.items():
                for dest in dest_states:
                    symbol = symbol if symbol != EPSILON else "ε"
                    G.add_edge(src, dest, label=symbol)

        pos = nx.spring_layout(G)
        plt.figure()
        node_colors = [G.nodes[n].get('color', 'blue') for n in G.nodes]
        nx.draw(G, pos, with_labels=True, node_shape="o", node_size=3000, font_size=10, node_color=node_colors)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        plt.show()
class State(object):
    def __repr__(self) -> str:
        return f"State({id(self)})"


def compile_regex(regex: str) -> NFA:
    # ASSUME no special chars (only regex like abc)
    nfa = NFA([], State())
    current = nfa.start
    for symbol in regex:
        new_state = State()
        nfa.add_state(new_state)
        nfa.add_transition(current, new_state, symbol)
        current = new_state
    nfa.add_accept(current)
    ST = State()
    OTHER = NFA([ST], ST)
    OTHER.add_transition(ST, ST, "xxd")
    nfa = nfa.concat(OTHER)
    return nfa


if __name__ == "__main__":
    nfa = compile_regex("abc")
    nfa.vizualize()
    assert nfa.match("abc")
    assert not nfa.match("ab")

