"""
Minecraft LegacyRandomSource Random Number Generator Python Implementation
Based on Java's Linear Congruential Generator (LCG) algorithm
"""

class LegacyRandomSource:
    """Simulates Minecraft's LegacyRandomSource random number generator"""

    MODULUS_BITS = 48
    MODULUS_MASK = (1 << 48) - 1  # 281474976710655
    MULTIPLIER = 25214903917
    INCREMENT = 11

    def __init__(self, seed: int = 0):
        self._seed = 0
        self.set_seed(seed)

    def set_seed(self, seed: int) -> None:
        """Set seed"""
        self._seed = (seed ^ self.MULTIPLIER) & self.MODULUS_MASK

    def next(self, bits: int) -> int:
        """Generate random number with specified bits"""
        self._seed = (self._seed * self.MULTIPLIER + self.INCREMENT) & self.MODULUS_MASK
        return self._seed >> (48 - bits)

    def next_int(self, bound: int = None) -> int:
        """Generate random integer"""
        if bound is None:
            return self._to_signed_int(self.next(32))

        if bound <= 0:
            raise ValueError("bound must be positive")

        if (bound & (bound - 1)) == 0:
            return (bound * self.next(31)) >> 31

        while True:
            bits = self.next(31)
            val = bits % bound
            if bits - val + (bound - 1) >= 0:
                return val

    def next_long(self) -> int:
        """Generate 64-bit random long integer"""
        # In Java: return ((long)this.next(32) << 32) + this.next(32);
        # CRITICAL: next(32) returns SIGNED int in Java!
        # When added to long, negative int is sign-extended
        high = self.next(32)
        low = self.next(32)
        # Convert low to signed int (Java behavior)
        low_signed = self._to_signed_int(low)
        # In Java: (long)high << 32 then + low_signed (sign-extended)
        result = (high << 32) + low_signed
        return self._to_signed_long(result & ((1 << 64) - 1))

    def next_float(self) -> float:
        """Generate random float between 0 and 1"""
        return self.next(24) / (1 << 24)

    def next_double(self) -> float:
        """Generate random double between 0 and 1"""
        high = self.next(26)
        low = self.next(27)
        return ((high << 27) + low) / (1 << 53)

    def next_boolean(self) -> bool:
        """Generate random boolean"""
        return self.next(1) != 0

    @staticmethod
    def _to_signed_int(value: int) -> int:
        """Convert unsigned 32-bit integer to signed integer"""
        if value >= (1 << 31):
            value -= (1 << 32)
        return value

    @staticmethod
    def _to_signed_long(value: int) -> int:
        """Convert unsigned 64-bit integer to signed long integer"""
        if value >= (1 << 63):
            value -= (1 << 64)
        return value


class WorldgenRandom(LegacyRandomSource):
    """Simulates Minecraft's WorldgenRandom for world generation"""

    def __init__(self, seed: int = 0):
        super().__init__(seed)

    def set_large_feature_seed(self, world_seed: int, x: int, z: int) -> None:
        """Set large feature seed"""
        self.set_seed(world_seed)
        m = self.next_long()
        n = self.next_long()
        # Must handle Java long overflow (64-bit signed)
        xm = self._to_signed_long((x * m) & ((1 << 64) - 1))
        zn = self._to_signed_long((z * n) & ((1 << 64) - 1))
        seed = xm ^ zn ^ world_seed
        seed = self._to_signed_long(seed & ((1 << 64) - 1))
        self.set_seed(seed)

    def set_large_feature_with_salt(self, world_seed: int, x: int, z: int, salt: int) -> None:
        """Set large feature seed with salt (for structure placement)"""
        seed = x * 341873128712 + z * 132897987541 + world_seed + salt
        seed = self._to_signed_long(seed & ((1 << 64) - 1))
        self.set_seed(seed)

    def set_decoration_seed(self, world_seed: int, x: int, z: int) -> int:
        """Set decoration seed"""
        self.set_seed(world_seed)
        m = self.next_long() | 1
        n = self.next_long() | 1
        seed = (x * m + z * n) ^ world_seed
        self.set_seed(seed)
        return seed

    def set_feature_seed(self, world_seed: int, x: int, z: int) -> None:
        """Set feature seed"""
        seed = world_seed + x + 10000 * z
        self.set_seed(seed)


def get_random_horizontal_direction(random: LegacyRandomSource) -> int:
    """Get random horizontal direction (0=NORTH, 1=EAST, 2=SOUTH, 3=WEST)"""
    return random.next_int(4)