import unittest
from v30core.agent_loop import AgentLoop, LoopConfig, LoopError


class ScriptedPlanner:
    def __init__(self, proposals):
        self.proposals = iter(proposals)

    def propose(self, state, findings, available_tools):
        return next(self.proposals)


def validator(state):
    if state.get("normalized") and state.get("audited"):
        return []
    out = []
    if not state.get("normalized"):
        out.append({"code": "NOT_NORMALIZED"})
    if not state.get("audited"):
        out.append({"code": "NOT_AUDITED"})
    return out


class AgentLoopTests(unittest.TestCase):
    def test_iterates_until_validation_passes(self):
        planner = ScriptedPlanner([
            {"action": "tool", "tool": "normalize", "args": {}},
            {"action": "tool", "tool": "audit", "args": {}},
        ])
        loop = AgentLoop(
            {"normalize": lambda _: {"normalized": True},
             "audit": lambda _: {"audited": True}},
            validator, planner
        )
        result = loop.run({})
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual([x["kind"] for x in result.trace],
                         ["tool", "validate", "tool", "validate"])

    def test_unknown_tool_is_rejected(self):
        loop = AgentLoop({}, validator, ScriptedPlanner([
            {"action": "tool", "tool": "shell", "args": {}}
        ]))
        with self.assertRaises(LoopError):
            loop.run({})

    def test_stop_returns_hold(self):
        loop = AgentLoop({}, validator, ScriptedPlanner([
            {"action": "stop", "reason": "requires user decision"}
        ]))
        self.assertEqual(loop.run({}).status, "HOLD")

    def test_max_steps_returns_hold(self):
        loop = AgentLoop({"noop": lambda _: {}}, validator,
                         ScriptedPlanner([{"action":"tool","tool":"noop","args":{}}] * 3),
                         LoopConfig(max_steps=2))
        result = loop.run({})
        self.assertEqual(result.status, "HOLD")
        self.assertEqual(result.trace[-1]["kind"], "max_steps")

    def test_repeated_action_guard(self):
        loop = AgentLoop({"noop": lambda _: {}}, validator,
                         ScriptedPlanner([{"action":"tool","tool":"noop","args":{}}] * 3),
                         LoopConfig(max_steps=5, max_repeated_action=1))
        result = loop.run({})
        self.assertEqual(result.status, "HOLD")
        self.assertEqual(result.trace[-1]["kind"], "loop_guard")


if __name__ == "__main__":
    unittest.main()
