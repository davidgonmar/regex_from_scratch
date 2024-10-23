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

    def concat(self, other: "NFA") -> "NFA":
        # concatenation is defined as
        # 1. add epsilon transition from accept states of self to start state of other
        # 2. add all states of other to self
        # that is, the resulting NFA will accept string that are accepted by self followed by other
        new_nfa = NFA(self.states, self.start)
        for state in self.accept:
            new_nfa.add_transition(state, other.start, EPSILON)
        new_nfa.states += other.states
        new_nfa.trasitions.update(other.trasitions)
        new_nfa.accept = other.accept
        return new_nfa


class State(object):
    def __repr__(self) -> str:
        return f"State({id(self)})"


def compile_regex(regex: str) -> NFA:
    states = []
    start = State()
    nfa = NFA(states, start)

    current_state = start
    for idx, symbol in enumerate(regex):
        if symbol == "*":  # * means 0 or more of previous symbol
            # add epsilon transition from current state to previous state
            nfa.add_transition(current_state, current_state, EPSILON)
        else:
            next_state = State()
            nfa.add_state(next_state)
            nfa.add_transition(current_state, next_state, symbol)
            current_state = next_state
            # if it is last symbol, add transition to accept state
            if idx == len(regex) - 1:
                nfa.add_accept(next_state)

    return nfa


if __name__ == "__main__":
    nfa = compile_regex("abc")
    assert nfa.match("abc")
    assert not nfa.match("ab")

    nfa = compile_regex("a*")
    assert nfa.match("a")
    assert nfa.match("aaaaa")
    # assert nfa.match("")
    assert not nfa.match("b")
    assert not nfa.match("ab")
