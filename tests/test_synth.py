#!/usr/bin/env python2

import unittest
from SNAPsynth import LMX2581

class TestPOCO(unittest.TestCase):
    def setUp(self):
        self.synth = LMX2581('localhost')

    def test_register_gen(self):
        # Codeloader hex files and associated frequencies
        hex_files = ['200MHz.txt', '250MHz.txt', '500MHz.txt', '200_1_3MHz.txt',
                     '200_3_4MHz.txt', '200_23124_123323MHz.txt']
        synth_freq = [200, 250, 500, 200+1./3, 200+3./4, 200+23124./123323]

        # Loop through the test cases.
        for fname, freq in zip(hex_files, synth_freq):
            print fname
            from_file = self.synth.get_registers(fname)
            from_gen = self.synth.gen_synth(freq, 10)

            # Check that both scripts are returning equally long sets of
            # register values and that they are all equal.
            self.assertEqual(len(from_file), len(from_gen))
            for idx, (f, g) in enumerate(zip(from_file, from_gen)):
                if f != g:
                    print self.synth.back_map[idx], f, g, hex(f), hex(g)
                    print bin(f)
                    print bin(g)
                    print
                self.assertEqual(f, g)

if __name__ == '__main__':
    unittest.main()
