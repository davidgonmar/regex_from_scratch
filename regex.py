from typing import Dict, Set, Hashable
from collections import defaultdict

NFAState = Hashable

EPSILON = ""


class NFA:
    def __init__(self, states: Set[NFAState], start: NFAState):
        self.states = states
        if start not in self.states:
            self.states.add(start)
        self.start = start
        self.accept = set()
        self.trasitions: Dict[NFAState, Dict[str, Set[NFAState]]] = defaultdict(
            lambda: defaultdict(set)
        )

    def add_transition(self, src: NFAState, dest: NFAState, symbol: str):
        self.trasitions[src][symbol].add(dest)

    def add_state(self, state: NFAState):
        self.states.add(state)

    def add_accept(self, state: NFAState):
        assert state in self.states, "State must be added before it can be accepted"
        self.accept.add(state)

    def epsilon_closure(self, states):
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for next_state in self.trasitions[state][EPSILON]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    def match(self, string: str) -> bool:
        current_states = {self.start}
        current_states = self.epsilon_closure(current_states)

        for symbol in string:
            next_states = set()
            for state in current_states:
                next_states |= self.trasitions[state][symbol]

            next_states = self.epsilon_closure(next_states)

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
        new_nfa.states |= other.states
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
        new_nfa.states |= other.states
        for accept in new_nfa.accept:
            new_nfa.add_transition(accept, other.start, EPSILON)

        # add the transactions of other
        for state, transitions in other.trasitions.items():
            for symbol, dest_states in transitions.items():
                for dest in dest_states:
                    new_nfa.add_transition(state, dest, symbol)
        new_nfa.accept = other.accept
        return new_nfa

    def star(self) -> "NFA":
        start_and_accept = State()
        new_nfa = self.copy()
        old_start = new_nfa.start
        new_nfa.start = start_and_accept
        new_nfa.add_state(start_and_accept)
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
            name, color, shape = str(state), "blue", "circle"
            if state == self.start and state in self.accept:
                name += "<start><accept>"
                color = "yellow"
            elif state == self.start:
                name += "<start>"
                color = "red"
            elif state in self.accept:
                name += "<accept>"
                color = "green"

            G.add_node(state, label=name, color=color, shape=shape)

        for src, transitions in self.trasitions.items():
            for symbol, dest_states in transitions.items():
                for dest in dest_states:
                    symbol = symbol if symbol != EPSILON else "ε"
                    G.add_edge(src, dest, label=symbol)

        pos = nx.spring_layout(G)
        plt.figure()
        node_colors = [G.nodes[n].get("color", "blue") for n in G.nodes]
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_shape="o",
            node_size=3000,
            font_size=10,
            node_color=node_colors,
        )
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        plt.show()


class State(object):
    name = None

    def __repr__(self) -> str:
        return f"State({self.name})" if self.name else f"State({id(self)})"

    def mark(self, name: str):
        self.name = name
        return self


def compile_regex(regex: str) -> NFA:
    # ASSUME no special chars (only regex like abc)

    index = 0

    def parse_single():
        nonlocal index
        if index >= len(regex):
            raise ValueError("Unexpected end of regex")
        symbol = regex[index]
        index += 1
        if symbol == "(":  # handle parenthesis
            nfa = parse_concat(regex)
            if index >= len(regex) or regex[index] != ")":
                raise ValueError("Expected closing parenthesis, but got end of regex")
            index += 1
        else:
            state1 = State()
            state2 = State()
            nfa = NFA({state1, state2}, state1)
            nfa.add_transition(state1, state2, symbol)
            nfa.add_accept(state2)

        # if there is a star after the symbol, apply the star operation
        if index < len(regex) and regex[index] == "*":
            index += 1
            nfa = nfa.star()
        return nfa

    def parse_concat(regex: str) -> NFA:
        nfa = parse_single()
        while index < len(regex) and regex[index] not in "|)":
            nfa = nfa.concat(parse_single())
        return nfa

    return parse_concat(regex)


if __name__ == "__main__":

    def test_simple():
        nfa = compile_regex("abc")
        assert nfa.match("abc")
        assert not nfa.match("ab")

    def test_star():
        nfa = compile_regex("a*")
        assert nfa.match("a")
        assert nfa.match("aa")
        assert nfa.match("")

        nfa = compile_regex("a*b")
        assert nfa.match("b")
        assert nfa.match("ab")
        assert nfa.match("aab")
        assert nfa.match("aaab")

    def test_star_and_parenthesis():
        nfa = compile_regex("(ab)*")
        nfa.vizualize()
        assert nfa.match("")
        assert nfa.match("ab")
        assert nfa.match("abab")
        assert nfa.match("ababab")
        assert not nfa.match("a")

    test_simple()
    test_star()
    test_star_and_parenthesis()
