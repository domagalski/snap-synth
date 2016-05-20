#!/usr/bin/env python2

################################################################################
## This module defines a class for interfacing with a the SNAP onboard synth.
## Copyright (C) 2014  Rachel Simone Domagalski: domagalski@berkeley.edu
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## ## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from corr import katcp_wrapper as _katcp

class LMX2581(_katcp.FpgaClient):
    """
    This interfaces with the TI LMX2581 synth chip, which can be
    controlled with KATCP writing to a software register.
    """
    def __init__(self, *args, **kwargs):
        # Open a connection to the ROACH and verify it.
        _katcp.FpgaClient.__init__(self, *args, **kwargs)

        # This is the reset register, according to Code Loader. This must be
        # written to the synth chip before the rest of the registers are
        # written. I'm not totally sure if I trust Code Loader, as all data
        # sheets say that the reset switch is on R5 and this number has the
        # address of R0, but let's burn that bridge when we get to it.
        self.reset = 1082589200

        # Set a blank register map. Parameters will be written in before sending
        # data to the synth. This is from page 29 of the LMX2581 datasheet:
        # http://www.ti.com/lit/ds/symlink/lmx2581.pdf
        #                           |   |   |   |   |   |   |   |
        # XXX I'm not impl
        self.registers = [int('0b00000000000000000000000000000000', 2), # R 0
                          int('0b00000000000000000000000000000001', 2), # R 1
                          int('0b00000100000000000000000000000010', 2), # R 2
                          int('0b00100000000000000000000000000011', 2), # R 3
                          int('0b00000000000000000000000000000100', 2), # R 4
                          int('0b00000000000000001010100000000101', 2), # R 5
                          int('0b00000000000000000000010000000110', 2), # R 6
                          int('0b00000000000000000000000000000111', 2), # R 7
                          int('0b00100000011111011101101111111000', 2), # R 8
                          int('0b00000011110001111100000000111001', 2), # R 9
                          int('0b00100001000000000101000011001010', 2), # R10
                          int('0b00000000000000000100000100001101', 2), # R13
                          int('0b00000010000111111110000000001111', 2)] # R15

    def from_codeloader(self, filename):
        """
        This function reads a file produced by Code Loader containing
        values to write to the lmx_ctrl register.
        """
        # Read in the lines from the file and convert them to integers
        # Assumptions: files have DOS line endings (made from Windows) and the
        # last thing in each line is a hex string.
        with open(filename) as f:
            nums = [int(l[-12:-2], 16) for l in f.readlines()]

        # Enable the synth
        self.write_int('adc16_use_synth', 1)

        for i, n in enumerate(nums):
            self.write_int('lmx_ctrl', n, True)
