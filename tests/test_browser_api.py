import json
import unittest
from browser_api import simulate_public
from cl_model import CramerLundbergModel

DEFAULT = {"u":20,"c":15,"lambda_rate":3,"mu_claim":4,"T":10,"runs":300,"seed":42}

class BrowserAdapterTests(unittest.TestCase):
    def test_matches_original_trace(self):
        result=json.loads(simulate_public(json.dumps(DEFAULT)))
        original=CramerLundbergModel(20,15,3,4,10,42).simulate()
        self.assertEqual(result['primary']['events'][0]['surplus'],original.events[0].surplus)
        self.assertEqual(result['primary']['ruinTime'],original.ruin_time)
        self.assertEqual(len(result['paths']),20)
        self.assertEqual(len(result['terminal']),300)

    def test_seed_is_reproducible(self):
        raw=json.dumps(DEFAULT)
        self.assertEqual(simulate_public(raw),simulate_public(raw))

    def test_invalid_numbers(self):
        for value in [float('nan'),float('inf'),-1,'20',True]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                simulate_public(json.dumps({**DEFAULT,'u':value}))

    def test_bounds_and_budget(self):
        for update in [{'runs':1001},{'seed':1.2},{'T':0},{'lambda_rate':100,'T':100,'runs':1000}]:
            with self.subTest(update=update),self.assertRaises(ValueError):
                simulate_public(json.dumps({**DEFAULT,**update}))

    def test_unknown_fields(self):
        with self.assertRaises(ValueError):simulate_public(json.dumps({**DEFAULT,'file':'x'}))

    def test_first_ruin_stops_path(self):
        result=json.loads(simulate_public(json.dumps({**DEFAULT,'u':0,'c':.01,'mu_claim':10000,'runs':1})))
        self.assertEqual(result['ruinedRuns'],1)
        self.assertLess(result['terminal'][0],0)
        self.assertEqual(len(result['primary']['events']),1)

if __name__=='__main__':unittest.main()
