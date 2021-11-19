from myplacer import MyPlacer
from mocker import RandomShapeGenerator, Symmetry, SquareShapeGenerator
from timeit import default_timer as timer


class SG1(RandomShapeGenerator):
    def __init__(self):
        super().__init__(radius = 10, rotations = Symmetry.none, fixed_seed = 111)

class SG2(RandomShapeGenerator):
    def __init__(self):
        super().__init__(radius = 10, rotations = Symmetry.twofold, fixed_seed = 121)

class SG3(RandomShapeGenerator):
    def __init__(self):
        super().__init__(radius = 10, rotations = Symmetry.threefold, fixed_seed = 113)

class SG4(RandomShapeGenerator):
    def __init__(self):
        super().__init__(radius = 10, rotations = Symmetry.sixfold, fixed_seed = 114)

class SG5(RandomShapeGenerator):
    def __init__(self):
        super().__init__(radius = 10, rotations = Symmetry.fourfold, fixed_seed = 115)

SFG_competition = [
    SG1,
    SG2,
    SG3,
    SG4,
    SG5,
]

start = timer()


filled = []
shapes = []
for i, o in enumerate(SFG_competition):
    mp = MyPlacer(o())
    sg = mp.run()
    filled.append(sg.filled_area)
    shapes.append(sg.placed_shapes)
    print("SG done")
end = timer()



print(f"Competition ended, my scores are: {filled}")
print(f"Average filled area: {sum(filled)/len(filled)}")
print(f"Time taken: {end - start}s, that is {(end - start) / sum(shapes)}s per shape") # Time in seconds, e.g. 5.38091952400282
