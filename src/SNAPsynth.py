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

import fractions as _frac
from math import log, log10, sqrt
from corr import katcp_wrapper as _katcp

class LMX2581(_katcp.FpgaClient):
    """
    This interfaces with the TI LMX2581 synth chip, which can be
    controlled with KATCP writing to a software register.
    """
    #def __init__(self, *args, **kwargs):
    #    # Open a connection to the ROACH and verify it.
    #    _katcp.FpgaClient.__init__(self, *args, **kwargs)

    def from_codeloader(self, filename):
        """
        This function reads a file produced by Code Loader containing
        values to write to the lmx_ctrl register.
        """
        self.lmx_write(self.get_registers(filename))

    def from_gen_synth(self, synth_mhz, ref_signal=10):
        """
        Generate a set of registers and write them into
        """
        self.lmx_write(self.gen_synth(synth_mhz, ref_signal))

    def get_registers(self, filename):
        """
        Read in the lines from the file and convert them to integers
        Assumptions: files have DOS line endings (made from Windows) and the
        last thing in each line is a hex string.
        """
        with open(filename) as f:
            registers = [int(l[-12:-2], 16) for l in f.readlines()]
        return registers

    def gen_registers(self, ref_signal, PLL_N, PLL_NUM, PLL_DEN, VCO_DIV,
                      PLL_R=1, OSC_2X=False, DLD_ERR_CNT=4, DLD_PASS_CNT=32,
                      FL_PINMODE=0, FL_INV=0, FL_SELECT=0,
                      MUXOUT_PINMODE=1, MUXOUT_INV=0, MUXOUT_SELECT=4,
                      LD_PINMODE=1, LD_INV=0, LD_SELECT=3, OUT_PWR=10):
        """
        This function is for precise fine-tuning of the registers.
        """
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
        # I literally have no idea what the following comment should mean.
        # XXX I'm not impl
        registers = [int('0b01000000100001110000000000010000', 2), # R5 (INIT)
                     int('0b00000010000111111110100000001111', 2), # R15
                     int('0b00000000000000000100000100001101', 2), # R13
                     int('0b00100001000000000101000011001010', 2), # R10
                     int('0b00000011110001111100000000111001', 2), # R 9
                     int('0b00100000011111011101101111111000', 2), # R 8
                     int('0b00000000000000000000000000000111', 2), # R 7
                     int('0b00000000000000000000010000000110', 2), # R 6
                     #int('0b00000000000000001010100000000101', 2), # R 5
        #                           |   |   |   |   |   |   |   |
                     int('0b00000000000000001000000000000101', 2), # R 5
                     int('0b00000000000000000000000000000100', 2), # R 4
                     int('0b00100000000000000000000000000011', 2), # R 3
                     int('0b00001100000000000000000000000010', 2), # R 2
                     int('0b11000000000000000000000000000001', 2), # R 1
                     int('0b00000000000000000000000000000000', 2)] # R 0

        reg_idx = {j:i+3 for i, j in enumerate(range(10, -1, -1))}
        reg_idx[13] = 2; reg_idx[15] = 1;
        reg_idx['rst'] = 0

        # Register R13: Page 30: 8.6.1.2.3
        freq_pd = ref_signal / PLL_R
        if freq_pd > 130:
            DLD_TOL = 0
        elif freq_pd > 80 and freq_pd < 130:
            DLD_TOL = 1
        elif freq_pd > 60 and freq_pd <= 80:
            DLD_TOL = 2
        elif freq_pd > 45 and freq_pd <= 60:
            DLD_TOL = 3
        elif freq_pd > 30 and freq_pd <= 45:
            DLD_TOL = 4
        else:
            DLD_TOL = 5

        # Set the register
        registers[reg_idx[13]] |= DLD_TOL << 15
        registers[reg_idx[13]] |= DLD_PASS_CNT << 18
        registers[reg_idx[13]] |= DLD_ERR_CNT << 28

        # Register R7 will just be tuned by the user. defaults are ok.
        registers[reg_idx[7]] |= LD_PINMODE << 4
        registers[reg_idx[7]] |= LD_INV << 7
        registers[reg_idx[7]] |= LD_SELECT << 8
        registers[reg_idx[7]] |= MUXOUT_PINMODE << 13
        registers[reg_idx[7]] |= MUXOUT_INV << 16
        registers[reg_idx[7]] |= MUXOUT_SELECT << 17
        registers[reg_idx[7]] |= FL_PINMODE << 23
        registers[reg_idx[7]] |= FL_INV << 22
        registers[reg_idx[7]] |= FL_SELECT << 25

        # Register R6
        # Codeloader seems to have 6 as the default readback address, and there
        # doesn't seem to be any good reason to change this.
        registers[reg_idx[6]] |= 6 << 5

        # Register R5
        BUFEN_DIS = 1 # I honestly can't remember why this is selected, but hey
        VCO_SEL_MODE = 1 # CodeLoader default

        # Select whether or not to use VCO_DIV. Use the same for both pins.
        OUT_MUX = int(VCO_DIV is not None)

        # Set is the oscillator frequency. This is from section 8.6.16 of the
        # data sheet (page 34). This formula I devised should give the correct
        # values for all cases.
        OSC_FREQ = min(max(0, int(log(ref_signal/32.0)/log(2))), 4)

        registers[reg_idx[5]] |= OUT_MUX << 11
        registers[reg_idx[5]] |= OUT_MUX << 13
        registers[reg_idx[5]] |= VCO_SEL_MODE << 15
        registers[reg_idx[5]] |= BUFEN_DIS << 20
        registers[reg_idx[5]] |= OSC_FREQ << 21

        # Register R4
        # XXX The defaults of my existing configs seem to work for this.

        # Register R3
        # Output A is the debugging output. Output B goes directly to the FPGA
        registers[reg_idx[3]] |= OUT_PWR << 6
        registers[reg_idx[3]] |= OUT_PWR << 12
        if VCO_DIV is not None:
            registers[reg_idx[3]] |= (VCO_DIV/2 - 1) << 18

        # Register R2
        registers[reg_idx[2]] |= PLL_DEN << 4

        # Register R1
        # XXX No idea what charge pump gain is, but for some reason, the top
        # two bits are set, so i gotta figure out why...
        # XXX Shouldn't I set the VCO_SEL to start at VCO 0? CodeLoader has it
        # start at VCO 3 for some reason even though the data sheet says to
        # start at VCO 0 if uncertain about it.
        VCO_SEL = 2
        # XXX The modulator order is something I need to actually determine how
        # to set, but I'm going to use a default for now.
        FRAC_ORDER = 2

        registers[reg_idx[1]] |= PLL_R << 4
        registers[reg_idx[1]] |= FRAC_ORDER << 12
        registers[reg_idx[1]] |= (PLL_NUM >> 12) << 15
        registers[reg_idx[1]] |= VCO_SEL << 25

        # Register R0
        # XXX By default, dithering should be disabled, but codeloader doesn't
        # seem to be following the data sheet.
        FRAC_DITHER = 2

        registers[reg_idx[0]] |= (PLL_NUM & ((1<<12)-1)) << 4
        registers[reg_idx[0]] |= PLL_N << 16
        registers[reg_idx[0]] |= FRAC_DITHER << 29

        # This variable is only referred to in my unit test.
        self.back_map = {v:k for k,v in zip(reg_idx.keys(), reg_idx.values())}

        # Return all of the registers in the proper order.
        return registers

    def gen_synth(self, synth_mhz, ref_signal, DLD_ERR_CNT=4, DLD_PASS_CNT=32):
        """
        This function sets the synth using a certain reference signal
        to oscillate at a new frequency
        """
        # Equation for the output frequency.
        # f_out = f_osc * OSC_2X / PLL_R * (PLL_N + PLL_NUM/PLL_DEN) / VCO_DIV
        # XXX Right now, I'm not going to use OSC_2X or PLL_R, so this becomes
        # f_out = f_osc * (PLL_N + PLL_NUM/PLL_DEN) / VCO_DIV

        # Get a good VCO_DIV. The minimum VCO frequency is 1800.
        vco_min = 1800; vco_max = 3800
        if synth_mhz > vco_min and synth_mhz < vco_max:
            VCO_DIV = None
        else:
            vco_guess = int(vco_min / synth_mhz) + 1
            VCO_DIV = vco_guess + vco_guess%2

        # Get PLLN, PLL_NUM, and PLL_DEN
        pll = (1 if VCO_DIV is None else VCO_DIV) * synth_mhz / ref_signal
        PLL_N = int(pll)
        frac = pll - PLL_N
        if frac < 1.0/(1<<22): # smallest fraction on the synth
            PLL_NUM = 0
            PLL_DEN = 1
        else:
            fraction = _frac.Fraction(frac).limit_denominator(1<<22)
            PLL_NUM = fraction.numerator
            PLL_DEN = fraction.denominator

        return self.gen_registers(ref_signal, PLL_N, PLL_NUM, PLL_DEN, VCO_DIV,
                                  DLD_ERR_CNT=DLD_ERR_CNT,
                                  DLD_PASS_CNT=DLD_PASS_CNT)

    def lmx_write(self, registers):
        """
        Write a set of registers to the synth.
        """
        # Enable the synth
        self.write_int('adc16_use_synth', 1)

        # Write register values from a file
        for i, n in enumerate(registers):
            self.write_int('lmx_ctrl', n, True)
