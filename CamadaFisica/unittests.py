import unittest
from BandaBase import encode_NRZ
from BandaBase import encode_Manchester
from BandaBase import encode_Bipolar
# Unit test
class TestEncodeNRZ(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(encode_NRZ("1010"), [1.0, -1.0, 1.0, -1.0])

    def test_all_ones(self):
        self.assertEqual(encode_NRZ("1111"), [1.0, 1.0, 1.0, 1.0])

    def test_all_zeros(self):
        self.assertEqual(encode_NRZ("000"), [-1.0, -1.0, -1.0])

    def test_empty_string(self):
        self.assertEqual(encode_NRZ(""), [])

    def test_mixed_sequence(self):
        self.assertEqual(encode_NRZ("010011"), [-1.0, 1.0, -1.0, -1.0, 1.0, 1.0])

class TestEncodeManchester(unittest.TestCase):
    def test_single_bit_1(self):
        # '1' → [1.0, -1.0]
        self.assertEqual(encode_Manchester("1"), [1.0, -1.0])

    def test_single_bit_0(self):
        # '0' → [-1.0, 1.0]
        self.assertEqual(encode_Manchester("0"), [-1.0, 1.0])

    def test_sequence_10(self):
        # '1' -> [1, -1], '0' -> [-1, 1]
        # total = [1, -1, -1, 1]
        self.assertEqual(encode_Manchester("10"), [1.0, -1.0, -1.0, 1.0])

    def test_sequence_01(self):
        # '0' -> [-1, 1], '1' -> [1, -1]
        # total = [-1, 1, 1, -1]
        self.assertEqual(encode_Manchester("01"), [-1.0, 1.0, 1.0, -1.0])

    def test_repeated_bits(self):
        # '111' → 3x [1, -1]
        self.assertEqual(encode_Manchester("111"), [1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
        # '000' → 3x [-1, 1]
        self.assertEqual(encode_Manchester("000"), [-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])

    def test_empty_string(self):
        # nenhuma entrada -> lista vazia
        self.assertEqual(encode_Manchester(""), [])


class TestEncodeBipolar(unittest.TestCase):
    def test_all_zeros(self):
        """Todos os bits 0 devem gerar apenas níveis 0.0"""
        self.assertEqual(encode_Bipolar("00000"), [0.0, 0.0, 0.0, 0.0, 0.0])

    def test_single_one(self):
        """Um único 1 deve gerar nível +1.0"""
        self.assertEqual(encode_Bipolar("1"), [1.0])

    def test_two_ones(self):
        """Dois bits 1 alternam entre +1.0 e -1.0"""
        self.assertEqual(encode_Bipolar("11"), [1.0, -1.0])

    def test_one_zero_mix(self):
        """Zeros mantêm nível 0.0, e 1s alternam"""
        self.assertEqual(encode_Bipolar("10101"), [1.0, 0.0, -1.0, 0.0, 1.0])

    def test_start_with_zero(self):
        """Começando com 0 deve gerar nível 0.0 e alternância correta depois"""
        self.assertEqual(encode_Bipolar("011"), [0.0, 1.0, -1.0])

    def test_long_pattern(self):
        """Padrão longo deve manter alternância correta"""
        bits = "1100110011"
        expected = [1.0, -1.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 1.0, -1.0]
        self.assertEqual(encode_Bipolar(bits), expected)

    def test_empty_input(self):
        """Entrada vazia deve retornar lista vazia"""
        self.assertEqual(encode_Bipolar(""), [])





if __name__ == "__main__":
    unittest.main()
